import pydicom
from __main__ import slicer
from slicer.ScriptedLoadableModule import *

try:
    import urlparse
except ImportError:
    import urllib


    class urlparse(object):
        urlparse = urllib.parse.urlparse
        parse_qs = urllib.parse.parse_qs

class DICOMRequestHandler(object):
    """
    Implements the mapping between DICOMweb endpoints
    and ctkDICOMDatabase api calls.
    """

    def __init__(self, logMessage):
        self.logMessage = logMessage
        self.logMessage('Starting DICOMRequestHandler')
        self.retrieveURLTag = pydicom.tag.Tag(0x00080190)
        self.numberOfStudyRelatedSeriesTag = pydicom.tag.Tag(0x00200206)
        self.numberOfStudyRelatedInstancesTag = pydicom.tag.Tag(0x00200208)

    def handleDICOMRequest(self, parsedURL, requestBody):
        contentType = b'text/plain'
        responseBody = None
        splitPath = parsedURL.path.split(b'/')
        if len(splitPath) > 2 and splitPath[2].startswith(b"studies"):
            self.logMessage('handling studies')
            contentType, responseBody = self.handleStudies(parsedURL, requestBody)
        elif len(splitPath) > 2 and splitPath[2].startswith(b"series"):
            pass
        else:
            self.logMessage('Looks like wadouri %s' % parsedURL.query)
            contentType, responseBody = self.handleWADOURI(parsedURL, requestBody)
        return contentType, responseBody

    def handleStudies(self, parsedURL, requestBody):
        contentType = b'application/json'
        splitPath = parsedURL.path.split(b'/')
        responseBody = b"[{}]"
        if len(splitPath) == 3:
            # studies qido search
            representativeSeries = None
            studyResponseString = b"["
            for patient in slicer.dicomDatabase.patients():
                for study in slicer.dicomDatabase.studiesForPatient(patient):
                    series = slicer.dicomDatabase.seriesForStudy(study)
                    numberOfStudyRelatedSeries = len(series)
                    numberOfStudyRelatedInstances = 0
                    modalitiesInStudy = set()
                    for serie in series:
                        seriesInstances = slicer.dicomDatabase.instancesForSeries(serie)
                        numberOfStudyRelatedInstances += len(seriesInstances)
                        if len(seriesInstances) > 0:
                            representativeSeries = serie
                            try:
                                dataset = pydicom.dcmread(slicer.dicomDatabase.fileForInstance(seriesInstances[0]),
                                                          stop_before_pixels=True)
                                modalitiesInStudy.add(dataset.Modality)
                            except AttributeError as e:
                                print('Could not get instance information for %s' % seriesInstances[0])
                                print(e)
                    if representativeSeries is None:
                        print('Could not find any instances for study %s' % study)
                        continue
                    instances = slicer.dicomDatabase.instancesForSeries(representativeSeries)
                    firstInstance = instances[0]
                    dataset = pydicom.dcmread(slicer.dicomDatabase.fileForInstance(firstInstance),
                                              stop_before_pixels=True)
                    studyDataset = pydicom.dataset.Dataset()
                    studyDataset.SpecificCharacterSet = [u'ISO_IR 100']
                    studyDataset.StudyDate = dataset.StudyDate
                    studyDataset.StudyTime = dataset.StudyTime
                    studyDataset.StudyDescription = dataset.StudyDescription
                    studyDataset.StudyInstanceUID = dataset.StudyInstanceUID
                    studyDataset.AccessionNumber = dataset.AccessionNumber
                    studyDataset.InstanceAvailability = u'ONLINE'
                    studyDataset.ModalitiesInStudy = list(modalitiesInStudy)
                    studyDataset.ReferringPhysicianName = dataset.ReferringPhysicianName
                    studyDataset[self.retrieveURLTag] = pydicom.dataelem.DataElement(
                        0x00080190, "UR", "TODO: provide WADO-RS RetrieveURL")
                    studyDataset.PatientName = dataset.PatientName
                    studyDataset.PatientID = dataset.PatientID
                    studyDataset.PatientBirthDate = dataset.PatientBirthDate
                    studyDataset.PatientSex = dataset.PatientSex
                    studyDataset.StudyID = dataset.StudyID
                    studyDataset[self.numberOfStudyRelatedSeriesTag] = pydicom.dataelem.DataElement(
                        self.numberOfStudyRelatedSeriesTag, "IS", str(numberOfStudyRelatedSeries))
                    studyDataset[self.numberOfStudyRelatedInstancesTag] = pydicom.dataelem.DataElement(
                        self.numberOfStudyRelatedInstancesTag, "IS", str(numberOfStudyRelatedInstances))
                    jsonDataset = studyDataset.to_json(studyDataset)
                    studyResponseString += jsonDataset.encode() + b","
            if studyResponseString.endswith(b','):
                studyResponseString = studyResponseString[:-1]
            studyResponseString += b']'
            responseBody = studyResponseString
        elif splitPath[4] == b'metadata':
            self.logMessage('returning metadata')
            contentType = b'application/json'
            responseBody = b"["
            studyUID = splitPath[3].decode()
            series = slicer.dicomDatabase.seriesForStudy(studyUID)
            for serie in series:
                seriesInstances = slicer.dicomDatabase.instancesForSeries(serie)
                for instance in seriesInstances:
                    dataset = pydicom.dcmread(slicer.dicomDatabase.fileForInstance(instance), stop_before_pixels=True)
                    jsonDataset = dataset.to_json()
                    responseBody += jsonDataset.encode() + b","
            if responseBody.endswith(b','):
                responseBody = responseBody[:-1]
            responseBody += b']'
        return contentType, responseBody

    def handleWADOURI(self, parsedURL, requestBody):
        q = urlparse.parse_qs(parsedURL.query)
        try:
            instanceUID = q[b'objectUID'][0].decode().strip()
        except KeyError:
            return None, None
        self.logMessage('found uid %s' % instanceUID)
        contentType = b'application/dicom'
        path = slicer.dicomDatabase.fileForInstance(instanceUID)
        fp = open(path, 'rb')
        responseBody = fp.read()
        fp.close()
        return contentType, responseBody