import os
import math
import logging
import logging.config

from ShpHelper import Layer
from ShpHelper import Geometry
from ShpHelper import GeomTypesShapely

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import MultiLineString

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


class WaveExposure:
    """
    This script calculates the wave exposure (without bathymetric data) according to the paper:

    Pepper, A. and Puotinen, M. L. (2009). GREMO: A GIS-based generic model for estimating relative wave exposure. The 18th World
    IMACS Congress and MODSIM09 International Congress on Modelling and Simulation (pp. 1964-1970). Cairns, Australia:
    Modelling and Simulation Society of Australia and New Zealand and IMACS.

    """

    length = 2000 #Length of the  in m
    deg = 15
    sourceFile = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        #self.logger.setLevel(logging.DEBUG)
        #self.logger.propagate = False

        # create console handler with a higher log level
        #ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        # add the handlers to the logger
        #self.logger.addHandler(ch)
        #logging.basicConfig(level=logging.DEBUG)
        self.logger.debug('WaveExposure Object created')

    def setRayLength(self,length):
        """Sets the lenght of the rays for wave exposure calculation"""
        self.logger.info('Set ray length to %i m' % length)
        self.length = length

    def getRayLength(self):
        """Returns the current length of rays"""
        return self.length


    def setDegree(self,deg):
        """Sets the degree spacing between the single rays"""
        self.logger.info('Set degree to %f°' % deg)
        self.deg = float(deg)


    def getDegree(self):
        """Returns the currently set degree"""
        return self.deg

    def setFilter(self,attributeFilter):
        self.logger.info('Set the filter to %s' % attributeFilter)
        self.attributeFilter = attributeFilter


    def getFilter(self):
        return self.attributeFilter
        

    def setSourceFile(self,source):
        self.logger.info('Set file path to %s' % source)
        if os.path.isfile(source):
            self.sourceFile = source
        else:
            raise FileNotFoundError('%s doesn\'t exist or is not a file' % source)
            self.logger.error('%s not found or not a file' % source)

    def checkComplete(self):
        if sourceFile is None:
            raise Exception('Source file is not selected')


    def startExposureCalculation(self):
        self.loadIslandData()

        #self.visitedIslands.writeShp('/home/kleinermann/workspace/dirk/gis/islands_visited.shp')


    def loadIslandData(self):
        self.logger.info('Start Exposure calculation')
        
        self.logger.info('Loading all Islands into Memory')
        self.logger.debug('Trying to load layer from file %s' % self.sourceFile)
        self.allIslandsLayer = Layer()
        self.allIslandsLayer.loadShp(self.sourceFile)

        self.logger.info('Loading all visisted Islands into Memory')
        self.visitedIslands = Layer()
        self.visitedIslands.loadShp(path = self.sourceFile, filter = self.attributeFilter)

        self.calcExposure(self.visitedIslands, self.allIslandsLayer)


    def calcExposure(self,visitedIslands,allIslands):
        self.logger.info('Start calculation of the wave exposure')
        
        self.logger.debug('Create a layer for the rays of the exposure')
        self.rayLayer = Layer()
        self.rayLayer.setGeometryType('MultiLineString')
        self.rayLayer.setSRS(allIslands.getSRS())
        self.rayLayer.setFields(allIslands.getFields())
        self.rayLayer.addField('FID', 'String')
        self.rayLayer.addField('Exposure', 'Float')


        #self.rayLayer.

        self.pointLayer = Layer()
        self.pointLayer.setGeometryType('Point')
        self.pointLayer.setSRS(allIslands.getSRS())
        self.pointLayer.setFields(allIslands.getFields())
        self.pointLayer.addField('FID', 'String')
        self.pointLayer.addField('Exposure', 'Float')

        for fid, geom in visitedIslands.geometries.items():
            self.logger.debug(type(geom))
            centroid = geom.getCentroid()
            exposureIsland = 0.0
            rayGeomList = []

            for curDeg in frange(0,360,self.deg):
                print('Current degree: %d' % curDeg)

                #Calculating the coordinate of the end point (depending on length)
                endPointx=centroid.x+(math.cos(math.radians(curDeg))*self.length)
                endPointy=centroid.y+(math.sin(math.radians(curDeg))*self.length)


                rayLong = LineString([(centroid.x,centroid.y),(endPointx,endPointy)])

                distance = self.length

                closestIntersectingPoint = None
                

                for ifid, igeom in allIslands.geometries.items():
                    if fid != ifid:
                        ipoly = igeom.getGeometry()
                        #checks if the previous created ray intersects with the boundary of an island
                        if rayLong.intersects(ipoly):
                            self.logger.debug("Line (%s) intersects with polygon (%s)" %(fid, ifid))
                            intersections = (rayLong.intersection(ipoly.boundary))

                            if intersections.geom_type == 'MultiPoint':
                                for poi in intersections:
                                    tempDistance = centroid.distance(poi)
                                    self.logger.debug("Intersection is a MultiPoint")

                                    if tempDistance < distance:
                                        distance = tempDistance
                                        closestIntersectingPoint = poi
                            elif intersections.geom_type == 'Point':
                                tempDistance = centroid.distance(intersections)
                                self.logger.debug("Intersection is onnly a point")

                                if tempDistance < distance:
                                    distance = tempDistance
                                    closestIntersectingPoint = intersections
                            else:
                                self.logger.debug("No intersections")
                    else:
                        pass

                self.logger.debug("Length of the ray: %f" % distance)
                
                exposureIsland += distance

                if distance != self.length:
                    self.logger.debug('Create LineString: %s,%s' % ((centroid.x,closestIntersectingPoint.x),(centroid.y,closestIntersectingPoint.y)))
                    rayGeomList.append(LineString([(centroid.x,centroid.y),(closestIntersectingPoint.x,closestIntersectingPoint.y)]))
                else:
                    self.logger.debug('Create LineString: %s,%s' % ((centroid.x,endPointx),(centroid.y,endPointy)))
                    rayGeomList.append(LineString([(centroid.x,centroid.y),(endPointx,endPointy)]))
            

            #Create MultiLine geometry
            self.logger.debug('Create the MultiLine geometry')
            self.logger.debug('List: %s' % rayGeomList)
            rayMultiLine = MultiLineString(rayGeomList)

            self.logger.debug('MultiLineString: %s' % rayMultiLine.length)
            
            rayAttributes = allIslands.getGeometryByFID(fid).getAttributes()
            rayAttributes['FID'] = fid
            rayAttributes['Exposure'] = exposureIsland

            
            

            self.rayLayer.addGeometry(fid,Geometry(rayMultiLine,fid,rayAttributes))


            #Create Point geometry
            self.logger.debug('Create Point geometry')

            centroidAttributes = allIslands.getGeometryByFID(fid).getAttributes()
            centroidAttributes['FID'] = fid
            centroidAttributes['Exposure'] = exposureIsland

            self.pointLayer.addGeometry(fid,Geometry(centroid,fid,centroidAttributes))


    def saveMultiLineLayer(self, filePath):
        if self.rayLayer is not None:
            self.rayLayer.writeShp(filePath)
        else:
            self.logger.error('MultiLine layer can\'t be saved because it is None. Start the exposure calculation to create the Layer first')
            raise TypeError('MultiLine layer can\'t be saved because it is None. Start the exposure calculation to create the Layer first')


    def savePointLayer(self, filePath):
        if self.pointLayer is not None:
            self.pointLayer.writeShp(filePath)
        else:
            self.logger.error('Point layer can\'t be saved because it is None. Start the exposure calculation to create the Layer first')
            raise TypeError('Point layer can\'t be saved because it is None. Start the exposure calculation to create the Layer first')



def main():
    logging.config.fileConfig('logging.conf')

    exposure = WaveExposure()

    exposure.setSourceFile('/home/kleinermann/Downloads/Vaestervik.shp')#dirk/gis/islands.shp')

    exposure.setFilter('visited = 1')

    exposure.startExposureCalculation()

    exposure.savePointLayer('/home/kleinermann/workspace/dirk/gis/points.shp')

    exposure.saveMultiLineLayer('/home/kleinermann/workspace/dirk/gis/multi.shp')
    
    #for key, point in visitedGeomDict.items():
    #   print('x: %f   y: %f' % (point.x,point.y))
    #geomtools.calcExposure(visitedIslands,allIslands,LENGTH,DEG)



if __name__ == "__main__":
    main()
    #print ('Start calculation')

    #logging.basicConfig(level=logging.DEBUG)