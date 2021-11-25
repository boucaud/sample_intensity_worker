import argparse
import json
import sys

import annotation_client.annotations as annotations
import annotation_client.tiles as tiles

import itk
import imageio


def main(datasetId, apiUrl, token, params):
    propertyName = params.get('customName', None)
    if not propertyName:
        propertyName = params.get('name', 'unknown_property')

    # Setup helper classes with url and credentials
    annotationClient = annotations.UPennContrastAnnotationClient(
        apiUrl=apiUrl, token=token)
    datasetClient = tiles.UPennContrastDataset(
        apiUrl=apiUrl, token=token, datasetId=datasetId)

    # Get all point annotations from the dataset
    annotationList = annotationClient.getAnnotationsByDatasetId(
        datasetId, shape='point')

    # Constants
    dim = 2
    radius = 5
    labelValue = 255
    ImageType = itk.Image[itk.UC, dim]
    SOType = itk.SpatialObject[dim]

    # Initialize ITK filters
    ellipse = itk.EllipseSpatialObject[dim].New()
    ellipse.SetRadiusInObjectSpace(radius)

    ellipseFilter = itk.SpatialObjectToImageFilter[SOType, ImageType].New(
        ellipse, InsideValue=labelValue, OutsideValue=0)

    statsFilter = itk.LabelStatisticsImageFilter[ImageType, ImageType].New()
    statsFilter.SetLabelInput(ellipseFilter.GetOutput())

    # Cache downloaded images by location
    images = {}

    for annotation in annotationList:
        # Get image location
        channel = annotation['channel']
        location = annotation['location']
        time, z, xy = location['Time'], location['Z'], location['XY']

        # Look for cached image. Initialize cache if necessary.
        image = images.setdefault(channel, {}).setdefault(
            time, {}).setdefault(z, {}).get(xy, None)

        if not image:
            # Download the image at specified location
            pngBuffer = datasetClient.getRawImage(xy, z, time, channel)
            # Read the png buffer
            decoded = imageio.imread(pngBuffer)
            # Create the itk Image
            image = itk.image_from_array(decoded)

            # Cache the itk image
            images[channel][time][z][xy] = image

        statsFilter.SetInput(image)
        ellipseFilter.SetSize(image.GetLargestPossibleRegion().GetSize())

        # Move our circle label
        geojsPoint = annotation['coordinates'][0]
        point = [geojsPoint['x'], geojsPoint['y']]
        ellipse.SetCenterInObjectSpace(point)

        ellipseFilter.Update()
        statsFilter.Update()

        # Send the new property value to the client
        annotationClient.addAnnotationPropertyValues(datasetId, annotation['_id'], {
                                                     propertyName: statsFilter.GetMean(labelValue)})


if __name__ == '__main__':

    # Define the command-line interface for the entry point
    parser = argparse.ArgumentParser(
        description='Compute average intensity values in a circle around point annotations')

    parser.add_argument('--datasetId', type=str, required=True, action='store')
    parser.add_argument('--apiUrl', type=str, required=True, action='store')
    parser.add_argument('--token', type=str, required=True, action='store')
    parser.add_argument('--parameters', type=str,
                        required=True, action='store')

    args = parser.parse_args(sys.argv[1:])

    main(args.datasetId, args.apiUrl, args.token, json.loads(args.parameters))
