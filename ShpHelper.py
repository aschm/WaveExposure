from enum import Enum
import logging
import os

import ogr
import osr

from shapely.geometry.base import BaseGeometry
from shapely import wkb

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step

def checkProjUnit(srs):
    """Checks the unit of the projection and raises an ValueError
        if it is not. The parameter is a OGR Spatial Reference"""
    if srs.GetAttrValue("UNIT",0) != 'metre':
        self.logger.error('The unit of the chosen projection %s does\'nt equal \'metres\'' % (srs))
        raise ValueError('The unit of the chosen projection does\'nt equal \'metres\'')



def getEPSG(srs):
    """Returns the EPSG-Code of the given srs from an OGR Spatial Reference"""
    return srs.GetAttrValue("AUTHORITY", 1)



def getShpFieldNames(shp, layerID = 0):
    """Opens shape file and returns all fields as List"""
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    source = driver.Open(filePath,layerID)
    layer = source.GetLayer(layerID)

    return getLayerFieldNames(layer)



def getLayerFieldNames(layer):
    """Returns all Field names of a ogr-layer"""
    fieldNames = []

    layerDefn = layer.GetLayerDefn()

    for i in range(layerDefn.GetFieldCount()):
        fieldNames.append(layerDefn.GetFieldDefn(i).GetName())

    return fieldNames



def getLayerFieldNamesAndType(layer):
    """Returns dict containing key = FieldName and value = FieldType"""

    fieldDict = {}

    layerDefn = layer.GetLayerDefn()

    for i in range(layerDefn.GetFieldCount()):
        key = layerDefn.GetFieldDefn(i).GetName()
        value = layerDefn.GetFieldDefn(i).GetType()
        fieldDict[key] = value


    return fieldDict


def getShpGeomType(shp,layerID):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    source = driver.Open(filePath,layerID)
    layer = source.GetLayer(layerID)

    return getLayerFieldNames(layer)


def getLayerGeomType(layer):
    return GeomTypesOgr(layer.GetGeomType())


def getFieldValueById(feature,id):
    ftype = feature.GetFieldDefnRef(id).GetType()
    name = feature.GetFieldDefnRef(id).GetName()

    #Integer
    if feature.GetFieldDefnRef(id).GetName() == 'FID':
        return feature.GetFID()
    elif ftype == ogr.OFTInteger or ftype == ogr.OFTInteger64:
        return feature.GetFieldAsInteger(id)
    #Real
    elif ftype == ogr.OFTReal:
        return feature.GetFieldAsDouble(id)
    #String
    elif ftype == ogr.OFTString:
        return feature.GetFieldAsString(id)
    #DateTime
    elif ftype == ogr.OFTDateTime:
        return feature.GetFieldAsDateTime(id)
    else:
        print('Field unknown')

        raise TypeError('Type %s not supported. Field name: %s. Type: %s' %(ftype,name,ogr.GetFieldTypeName(ftype)))


class GeomTypesOgr(Enum):
    Unknown = 0
    Point = 1
    LineString = 2
    Polygon = 3
    MultiPoint = 4
    MultiLineString = 5
    MultiPolygon = 6
    GeometryCollection = 7
    LinearRing = 101



class GeomTypesShapely(Enum):
    Unknown = 0
    Point = 1
    Line = 2
    Polygon = 3
    MultiPoint = 4
    MultiLine = 5
    MultiPolygon = 6
    GeometryCollection = 7
    LinearRing = 101


"""
Represents

"""
class Geometry:
    
    def __init__(self,geom,fid = None,attributes = {},logger = None):
        self.logger = logger or logging.getLogger(__name__+'.Geometry')

        self.logger.debug('Create new Geometry')

        if isinstance(geom, ogr.Geometry):
            #For OGR Geometries which need to be changed to shapely
            self.logger.debug('Add ogr.Geometry with FID %s' % fid)
            self.parseOGRGeometry(geom)
        elif isinstance(geom, BaseGeometry):
            self.geom = geom
        else:
            self.geomLogger.error('Object %s is not of type ogr.Geometry or shapely.BaseGeometry' % type(geom))
            raise TypeError('Object must be of type ogr.Geometry or shapely.BaseGeometry')
        self.fid = fid
        self.attributes = attributes



    def parseOGRGeometry(self,geom):
        """Loads a OGR Geometry and stores it as Shapely Geometry."""
        self.logger.debug('Convert ogr.Geometry to Shapely Geometry')
        wkbGeom = geom.ExportToWkb()
        self.geom = wkb.loads(wkbGeom)


    def setGeometry(self,geom):
        self.geom = geom


    def getGeometry(self):
        return self.geom

    def getCentroid(self):
        return self.geom.centroid

    """
    Adds an Attribute
      - if the Attribute is not part of the layers fields it won't
        be persisted)
    """
    def addAttribute(self,name,value):
        if not isinstance(name, str):
            raise TypeError('Attribute name has to be of the type String and not %s' % type(name))
        elif name in attributes:
            self.geomLogger.error('Attribute %s of the geometry with fid %s exists already' %(name,fid))
            raise ValueError('Key %s already exist in dict attributes use update' % name)
        
        self.attributes[name] = value


    def getAttributes(self):
        return self.attributes

    """
    Updates an existing attribute
    """
    def updateAttribute(self,name,value):
        if not isinstance(name, str):
            raise TypeError('Attribute name has to be of the type String and not %s' % type(name))
        elif name not in attributes:
            self.geomLogger.error('Overwriting attribute %s of the geometry with fid %s' %(name,fid))
            raise ValueError('Can\'t find key %s in Dictionary attributes' % name)

        self.attributes[name] = value


    """
    Removes an attribute from the Geometry
    """
    def delAttribute(self,name):
        if not isinstance(name, str):
            raise TypeError('Attribute name has to be of the type String and not %s' % type(name))
        elif name in attributes:
            self.geomLogger.warning('Overwriting attribute %s of the geometry with fid %s' %(name,fid))

        del self.attributes[name]
    
    def __repr__(self):
        return "<WaveExposure.Geometry fid: %s, geom: %s, attributes: %s>" % (fid,geom,attributes)


class Layer:
    """
    Represents a layer from OGR (GDAL) as layer in an easy Shapely-Python construct

    Includes methods to easily read/store GDAL-Layers
    """


    
    def __init__(self,logger = None):
        self.logger = logger or logging.getLogger(__name__+'.Layer')
        self.logger.debug('New Layer is created')
        self.geometries = {}
        self.fields = {}
        self.srs = None
        self.geometryType = None

    def setGeometryType(self,geometryType):
        """Sets the type of the Geometry"""
        self.logger.debug("Set the geometry type: %s" % geometryType)
        self.geometryType = geometryType


    def getGeomType(self):
        """Returns the geometry type"""
        return self.geometryType


    def setSRS(self,srs):
        """Sets the srs of the current layer"""
        self.logger.debug("Set the srs to %s" % srs)
        self.srs = srs

    def getSRS(self):
        """Returns the srs of the Layer"""
        return self.srs

    def setFields(self,fields):
        """Sets the attribute dict of the Layer to the given dict"""
        self.fields = fields

    def getFields(self):
        """Returns the field dict"""
        return self.fields

    def addField(self,name,varType):
        """Adds a field to the  field dict with a given Type"""
        self.logger.debug('Add field %s with the type %s' %(name,varType))
        if varType == 'Integer':
            vType = ogr.OFTInteger
        elif varType == 'Float':
            vType = ogr.OFTReal
        #String
        elif varType == 'String':
            vType = ogr.OFTString
        #DateTime
        elif varType == 'DateTime':
            vType = ogr.OFTDateTime
        else:
            self.logger.error('Field Type %s unknown' % varType)
            raise TypeError('Type %s not supported' % type)

        self.fields[name] = vType

    def removeField(self,name):
        try:
            del self.fields[name]
        except KeyError:
            self.logger.error("Field %s doesn't exist in this Layer and can't be deleted" % name)


    def addGeometry(self,fid,geom):
        if isinstance(geom,Geometry):
            self.geometries[fid] = geom
        else:
            self.logger.error('%s is not of type ShpHelper.Geometry' % type(geom))
            raise TypeError('Given Geometry of type %s is not of type ShpHelper.Geometry' % type(geom))
    

    def getGeometryByFID(self,fid):
        try:
            return self.geometries[fid]
        except KeyError:
            self.logger.error('FID %s not in Layer' % fid)
            self.logger.debug(self.geometries.keys())
            raise KeyError('FID %s not in Layer' % fid)



    def loadShp(self,path, layerID = 0, filter = None):
        driver = ogr.GetDriverByName("ESRI Shapefile")
        self.logger.debug('Trying to open %s with OGR' % path)
        source = driver.Open(path,0)
        layer = source.GetLayer(layerID)
        
        self.logger.debug('Layer - Name: %s' % (layer.GetName()))
        
        #Checks the unit of the projection and reads the EPSG-Code
        self.srs = layer.GetSpatialRef()
        #self.logger.debug(srs)
        #srs.checkProjUnit(srs)
        #self.epsg = getEPSG(srs)
        #logging.debug('Layer - EPSG: %s' % self.epsg)

        #Gets the geometry type of the layer
        self.geometryType = GeomTypesOgr(layer.GetGeomType()).name
        self.logger.debug('OGC Thing: %s' % GeomTypesOgr(layer.GetGeomType()).name)
        self.logger.debug('Layer - Geometry Type: %s' % self.geometryType)
        

        #Get the names and types of all fields
        self.fields = getLayerFieldNamesAndType(layer)

        if filter is not None:
            self.logger.debug('Set attribute filter: %s' % filter)
            layer.SetAttributeFilter(filter)


        #Loads all features of the layer and adds them to the feature list
        for feature in layer:
            #Get Geometry
            geom = feature.GetGeometryRef()
            #Get FID
            fid = feature.GetFID()

            attributes = {}
            self.logger.debug(self.fields)

            #Get all attributes of the Geometry
            for fieldName in self.fields.keys():
                #if fieldName != 'FID':
                fieldId = feature.GetFieldIndex(fieldName)
                    
                attributes[fieldName] = getFieldValueById(feature,fieldName)
                print(attributes)

            self.logger.debug('Create ShpHelper.Geometry with FID %s' % fid)
            self.geometries[fid] = Geometry(geom,fid,attributes)


            #print('Length allISlandDict' % allIslandsGeomDict.length())

        del source

        #self.logger.debug(self.geometries['177'].geom)

    def writeShp(self, filePath):
        driver = ogr.GetDriverByName("ESRI Shapefile")

        self.logger.debug('File %s exitst? %s' % (filePath,os.path.exists(filePath)))
        if os.path.exists(filePath):
            driver.DeleteDataSource(filePath)
            self.logger.info('Deleting %s... ' % (filePath))

        source = driver.CreateDataSource(filePath)

        layerName = os.path.splitext(os.path.basename(filePath))[0]
        
        self.logger.debug('Layername: %s' % layerName)
        self.logger.debug('SRS: %s' % self.srs)
        self.logger.debug('GeomType: %s' % GeomTypesOgr[self.geometryType].value)
        layer = source.CreateLayer(layerName,self.srs,GeomTypesOgr[self.geometryType].value)

        for fieldName, fieldType in self.fields.items():

            field = ogr.FieldDefn(fieldName, fieldType)

            if fieldType == ogr.OFTString:
                field.SetWidth(80)

            layer.CreateField(field)

        for fid, geometry in self.geometries.items():
            feature =  ogr.Feature(layer.GetLayerDefn())
            
            geom = ogr.CreateGeometryFromWkb(wkb.dumps(geometry.geom))
            feature.SetGeometry(geom)

            self.logger.debug('Feature ID (Geometry): %s' % type(fid))
            feature.SetFID(int(fid))
            #feature.SetField('FID',ogr.OFTInteger)
            self.logger.debug('Feature ID (OGR): %i' % feature.GetFID())

            for attributeName, attributeValue in geometry.attributes.items():
                self.logger.debug('Attribute: %s Value:%s' % (attributeName, attributeValue))
                feature.SetField(attributeName,attributeValue)



            layer.CreateFeature(feature)

            feature.Destroy()

        del source


if __name__ == '__main__':
    pass