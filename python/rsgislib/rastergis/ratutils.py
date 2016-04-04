#!/usr/bin/env python


############################################################################
#  ratutils.py
#
#  Copyright 2013 RSGISLib.
#
#  RSGISLib: 'The remote sensing and GIS Software Library'
#
#  RSGISLib is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  RSGISLib is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with RSGISLib.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Purpose:  Provide a set of utilities which combine commands to create
#           useful extra functionality and make it more easily available
#           to be reused.
#
# Author: Dan Clewley
# Email: daniel.clewley@gmail.com
# Date: 16/11/2013
# Version: 1.1
#
# History:
# Version 1.0 - Created.
# Version 1.1 - Update to be included into RSGISLib python modules tree
#               (By Pete Bunting).
#
############################################################################

import sys
import math
import os.path
import shutil
from enum import Enum
import rsgislib
from rsgislib import rastergis
from rsgislib import vectorutils
from rsgislib import imageutils
from rsgislib import segmentation

haveGDALPy = True
try:
    import osgeo.gdal as gdal
except ImportError as gdalErr:
    haveGDALPy = False
    
    
haveGDALOGRPy = True
try:
    from osgeo import ogr
    from osgeo import osr
except ImportError as gdalogrErr:
    haveGDALOGRPy = False

haveMatPlotLib = True
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mClrs
except ImportError as pltErr:
    haveMatPlotLib = False   
    
haveNumpy = True
try:
    import numpy
except ImportError as numErr:
    haveNumpy = False

haveHDF5 = True
try:
    import h5py
except ImportError as h5Err:
    haveHDF5 = False
    
haveScipyStats = True
try:
    import scipy.stats
except ImportError as scipystatsErr:
    haveScipyStats = False
    
haveRIOSRat = True
try:
    from rios import rat
    from rios import ratapplier
except ImportError as riosRatErr:
    haveRIOSRat = False

haveSKLearnPCA = True
try:
    from sklearn.decomposition import PCA
except ImportError as sklearnPCAErr:
    haveSKLearnPCA = False




class RSGISRATThresMeasure(Enum):
    kurtosis = 1
    skewness = 2
    combined = 3
    auto = 4
    
class RSGISRATThresDirection(Enum):
    lower = 1
    upper = 2
    lowerupper = 3


def populateImageStats(inputImage, clumpsFile, outascii=None, threshold=0.0, calcMin=False, calcMax=False, calcSum=False, calcMean=False, calcStDev=False, calcMedian=False, calcCount=False, calcArea=False, calcLength=False, calcWidth=False, calcLengthWidth=False):
    
    """ Attribute RAT with statistics from from all bands in an input image.

Where:

* inputImage - input image to calculate statistics from, if band names are avaialble these will be used for attribute names in the output RAT.
* clumpsFile - input clumps file, statistics are added to RAT.
* threshold - float, values below this are ignored (default=0)
* outascii - string providing output CSV file (optional).
* calcMin - Calculate minimum
* calcMax - Calculate maximum
* calcSum - Calculate sum
* calcMean - Calculate mean
* calcStDev - Calculate standard deviation

Example::

    from rsgislib.rastergis import ratutils
    inputImage = 'jers1palsar_stack.kea'
    clumpsFile = 'jers1palsar_stack_clumps_elim_final.kea'
    ratutils.populateImageStats(inputImage, clumpsFile, calcMean=True)

    """
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings required for this function could not be imported\n\t" + gdalErr)
    
    # Open image
    dataset = gdal.Open(inputImage, gdal.GA_ReadOnly)
    
    # Set up list to hold statistics to calculate
    stats2Calc = list()
    
    # Loop through number of bands in image
    nBands = dataset.RasterCount

    # Set up array to hold all column names (used when exporting to ASCII)
    outFieldsList = []
    
    for i in range(nBands):
        bandName = dataset.GetRasterBand(i+1).GetDescription()
        # If band name is not set set to bandN
        if bandName == '':
            bandName = 'Band' + str(i+1)

        # Initialise stats to calculate at None
        minName = None
        maxName = None
        sumName = None
        meanName = None
        stDevName = None
        medianName = None
        countName = None

        if calcMin:
            minName = bandName + 'Min'
            outFieldsList.append(minName)
        if calcMax:
            maxName = bandName + 'Max'
            outFieldsList.append(maxName)
        if calcSum:
            sumName = bandName + 'Sum'
            outFieldsList.append(sumName)
        if calcMean:
            meanName = bandName + 'Avg'
            outFieldsList.append(meanName)
        if calcStDev:
            stDevName = bandName + 'Std'
            outFieldsList.append(stDevName)
        if calcMedian:
            raise Exception('Median is not currently supported.')
            medianName = bandName + 'Med'
            outFieldsList.append(medianName)
        if calcCount:
            raise Exception('Count is not currently supported.')
            countName = bandName + 'Pix'
            outFieldsList.append(countName)

        stats2Calc.append(rastergis.BandAttStats(band=i+1, 
                    minField=minName, maxField=maxName, 
                    sumField=sumName, stdDevField=stDevName, 
                    meanField=meanName))
    
    # Calc stats
    print('''Calculating statistics for %i Bands'''%(nBands))
    t = rsgislib.RSGISTime()
    t.start(True)
    rastergis.populateRATWithStats(inputImage, clumpsFile, stats2Calc)
    t.end()

    # Calculate shapes, if required
    if calcArea or calcLength or calcWidth or calcLengthWidth:
        raise Exception('Shape features are not currently supported.')
        print("\nCalculating shape indices")
        shapes = list()
        if calcArea:
            shapes.append(rastergis.ShapeIndex(colName="Area", idx=rsgislib.SHAPE_SHAPEAREA))
            outFieldsList.append("Area")
        if calcLength:
            shapes.append(rastergis.ShapeIndex(colName="Length", idx=rsgislib.SHAPE_LENGTH))
            outFieldsList.append("Length")
        if calcWidth:
            shapes.append(rastergis.ShapeIndex(colName="Width", idx=rsgislib.SHAPE_WIDTH))
            outFieldsList.append("Width")
        if calcLengthWidth:
            shapes.append(rastergis.ShapeIndex(colName="LengthWidthRatio", idx=rsgislib.SHAPE_LENGTHWIDTH))
            outFieldsList.append("LengthWidthRatio")

        t.start(True)
        rastergis.calcShapeIndices(clumpsFile, shapes)
        t.end()
    
    # Export to ASCII if required
    if outascii is not None:
        print("\nExporting as ASCII")
        t.start(True)
        rastergis.export2Ascii(clumpsFile, outascii, outFieldsList)
        t.end()




def calcPlotGaussianHistoModel(clumpsFile, outGausH5File, outHistH5File, outPlotFile, varCol, binWidth, classColumn, classVal, plotTitle):
    """ Extracts a column from the RAT, masking by a class calculating the histogram and 
        fitting a Gaussian mixture model to the histogram. Outputs include a plot and HDF5
        files of the histogram and gaussian parameters.

Where:

* clumpsFile - input clumps file with populated RAT.
* outGausH5File - the output HDF5 file for the Gaussian Mixture Model
* outHistH5File - the output HDF5 file for the histogram.
* outPlotFile - the output PDF file for the plot
* varCol - Column within the RAT for the variable to be used for the histogram
* binWidth - Bin width for the histogram
* classColumn - Column where the classes are specified
* classVal - Class used to mask the input variable
* plotTitle - title for the plot

Example::

    from rsgislib.rastergis import ratutils
    
    clumpsFile = "FrenchGuiana_10_ALL_sl_HH_lee_UTM_mosaic_dB_segs.kea"
    outGausH5File = "gaufit.h5"
    outHistH5File = "histfile.h5"
    outPlotFile = "Plot.pdf"
    varCol = "HVdB"
    binWidth = 0.1
    classColumn = "Classes"
    classVal = "Mangrove"
    plotTitle = "HV dB Backscater from Mangroves; French Guiana"
    
    ratutils.calcPlotGaussianHistoModel(clumpsFile, outGausH5File, outHistH5File, outPlotFile, varCol, binWidth, classColumn, classVal, plotTitle)

    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings required for this function could not be imported\n\t" + gdalErr)
    # Check matplotlib is available
    if not haveMatPlotLib:
        raise Exception("The matplotlib module is required for this function could not be imported\n\t" + pltErr)       
    # Check hdf5 is available
    if not haveHDF5:
        raise Exception("The hdf5 module is required for this function could not be imported\n\t" + h5Err)
        
    # Calculate histogram and fit Gaussian Mixture Model
    rastergis.fitHistGausianMixtureModel(clumps=clumpsFile, outH5File=outGausH5File, outHistFile=outHistH5File, varCol=varCol, binWidth=binWidth, classColumn=classColumn, classVal=classVal)
    
    
    if not h5py.is_hdf5(outGausH5File):
        raise Exception(outGausH5File + " is not a HDF5 file.")
        
    if not h5py.is_hdf5(outHistH5File):
        raise Exception(outHistH5File + " is not a HDF5 file.")

    gausFile = h5py.File(outGausH5File,'r')
    gausParams = gausFile['/DATA/DATA']
    
    
    histFile = h5py.File(outHistH5File,'r')
    histData = histFile['/DATA/DATA']
    
    xVals = []
    xValsHist = []
    histBins = []
    
    for histBin in histData:
        xValsHist.append(histBin[0]-(binWidth/2))
        xVals.append(histBin[0])
        histBins.append(histBin[1])
            
    gAmpVals = []
    gFWHMVals = []
    gOffVals = []
    gNoiseVals = []
    noiseVal = 0.0
    
    for gausParam in gausParams:
        gOffVals.append(gausParam[0])
        gAmpVals.append(gausParam[1])
        gFWHMVals.append(gausParam[2])
        noiseVal = gausParam[3]
    
    fig, ax = plt.subplots()
    histBars = ax.bar(xValsHist, histBins, width=binWidth, color='#A7A7A7', edgecolor='#A7A7A7')
    
    predVals = numpy.zeros(len(xVals))
    for i in range(len(xVals)):
        gNoiseVals.append(noiseVal)
        for j in range(len(gOffVals)):
            predVals[i] = predVals[i] + (gAmpVals[j] * math.exp((-1.0)*(pow(xVals[i] - gOffVals[j], 2)/(2.0 * pow(gFWHMVals[j], 2)))))
        predVals[i] = predVals[i] + noiseVal
    
    ax.plot(xVals, predVals, color='red')
    ax.plot(xVals, gNoiseVals, color='blue', linestyle='dashed')
    
    ax.set_ylabel('Freq.')
    ax.set_title(plotTitle)
    plt.savefig(outPlotFile, format='PDF')
    
    gausFile.close()
    histFile.close()
    
    
    
def findChangeClumpsHistSkewKurtTest(inputClumps, inClassCol, classOfInterest, changeVarCol, outChangeFeatCol, noDataVals=[], thresMeasure=RSGISRATThresMeasure.auto, exportPlot=None, showAllThreshPlot=False):
    """
    This function identifies potential change features from both sides of the histogram 
    by slicing the histogram and finding an optimal skewness and kurtosis.
    
    Where:
    
    * inputClumps - input clumps file.
    * inClassCol - The column specifiying the classes, one of which change will be found.
    * classOfInterest - The class (as defined in inClassCol) on which changed is being found.
    * changeVarCol - Variable(s) to be used to find change. Expecting column name. Needs to be numeric. If a list of column names is provided then they are combined using PCA and the first PC is used for the change process.
    * outChangeFeatCol - the output column. Regions lower than lower threshold have value 1. Regions higher than upper threshold have value 2. No change had threshold 0.
    * noDataVals - list of no data values to be ignored.
    * thresMeasure - needs to be of type RSGISRATThresMeasure (default is auto)
    * exportPlot - file name for exporting a histogram plot with thresholds annotated. No plot is create if None is passed (default is none).
    * showAllThreshPlot - option when plotting to put all the thresholds on to the plot rather than just the one being used.
    
    Return:
    * list of lower [0] and upper [1] thresholds used to define the no change region.
    
    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    # Check scipy stats is available
    if not haveScipyStats:
        raise Exception("The scipy stats is required for this function could not be imported\n\t" + scipystatsErr)
    if not exportPlot == None:
        # Check matplotlib is available
        if not haveMatPlotLib:
            raise Exception("The matplotlib module is required for this function could not be imported\n\t" + pltErr)
    if type(changeVarCol) is list:
        if not haveSKLearnPCA:
            raise Exception("The scikit learn library PCA module is required when a list of column variables is given\n\t" + sklearnPCAErr)

    ## Open the image file...
    ratDataset = gdal.Open(inputClumps, gdal.GA_Update)

    ## Read in columns
    classVals = rat.readColumn(ratDataset, inClassCol)
    outChangeFeats = numpy.zeros_like(classVals)
    ID = numpy.arange(classVals.shape[0])
    
    vals = None
    if type(changeVarCol) is list:
        numVars = len(changeVarCol)
        numRows = classVals.shape[0]
        varVals = numpy.zeros((numVars,numRows), dtype=numpy.float)
        i = 0
        for varCol in changeVarCol:
            colVals = rat.readColumn(ratDataset, varCol)
            varVals[i] = colVals
            i = i + 1
        varVals = varVals.transpose()
        
        ID = ID[classVals == classOfInterest]
        varVals = varVals[(classVals == classOfInterest)]
        
        ID = ID[numpy.isfinite(varVals).all(axis=1)]
        varVals = varVals[numpy.isfinite(varVals).all(axis=1)]
        
        for noDataVal in noDataVals:
            ID = ID[(varVals != noDataVal).all(axis=1)]
            varVals = varVals[(varVals != noDataVal).all(axis=1)]
        
        pca = PCA(n_components=1)
        fittedPCA = pca.fit(varVals)
    
        vals = fittedPCA.transform(varVals)[:,0]
    else:
        vals = rat.readColumn(ratDataset, changeVarCol)        
    
        ID = ID[classVals == classOfInterest]
        if ID.shape[0] == 0:
            rat.writeColumn(ratDataset, outChangeFeatCol, outChangeFeats)
            return
        vals = vals[classVals == classOfInterest]
        
        ID = ID[numpy.isfinite(vals)]
        vals = vals[numpy.isfinite(vals)]
        
        for noDataVal in noDataVals:
            ID = ID[vals != noDataVal]
            vals = vals[vals != noDataVal]
    
    n = vals.shape[0]
    lq = numpy.percentile(vals, 25)
    uq = numpy.percentile(vals, 75)
    iqr = uq - lq
    binSize = 2 * iqr * n**(-1/3)
    print("Bin Size = ", binSize)
    numBins = int((numpy.max(vals) - numpy.min(vals))/binSize)+2
    print("num of bins = ", numBins)
    
    hist, bin_edges = numpy.histogram(vals, bins=numBins)
    
    print(hist.shape)
    print(bin_edges.shape)
        
    print("LQ = ", lq)
    print("UQ = ", uq)
    
    lqNumBins = int((lq - bin_edges[0])/binSize)+1
    uqNumBins = int((bin_edges[-1]-uq)/binSize)+1
    
    print("lqNumBins = ", lqNumBins)
    print("uqNumBins = ", uqNumBins)
    
    kurtosisVals = numpy.zeros((lqNumBins,uqNumBins), dtype=numpy.float)
    skewnessVals = numpy.zeros((lqNumBins,uqNumBins), dtype=numpy.float)
    lowBins = numpy.zeros((lqNumBins,uqNumBins), dtype=numpy.int)
    upBins = numpy.zeros((lqNumBins,uqNumBins), dtype=numpy.int)
    
    for lowBin in range(lqNumBins):
        for upBin in range(uqNumBins):
            #print("Bin [" + str(lowBin) + ", " + str(numBins-upBin) + "]")
            histTmp = hist[lowBin:(numBins-upBin)]
            #print(histTmp)
            #print(histTmp.shape)
            lowBins[lowBin,upBin] = lowBin
            upBins[lowBin,upBin] = numBins-upBin
            
            kurtosisVals[lowBin,upBin] = scipy.stats.kurtosis(histTmp)
            skewnessVals[lowBin,upBin] = scipy.stats.skew(histTmp)
            
    
    #print(kurtosisVals)
    #print(skewnessVals)
    kurtosisValsAbs = numpy.absolute(kurtosisVals)
    skewnessValsAbs = numpy.absolute(skewnessVals)
    #print("Kurtosis Range: [" + str(numpy.min(kurtosisValsAbs)) + ", " + str(numpy.max(kurtosisValsAbs)) + "]") 
    #print("Skewness Range: [" + str(numpy.min(skewnessValsAbs)) + ", " + str(numpy.max(skewnessValsAbs)) + "]") 
    kurtosisValsNorm = (kurtosisValsAbs-numpy.min(kurtosisValsAbs)) / (numpy.max(kurtosisValsAbs)-numpy.min(kurtosisValsAbs))
    skewnessValsNorm = (skewnessValsAbs-numpy.min(skewnessValsAbs)) / (numpy.max(skewnessValsAbs)-numpy.min(skewnessValsAbs))
    
    #print("Kurtosis Norm Range: [" + str(numpy.min(kurtosisValsNorm)) + ", " + str(numpy.max(kurtosisValsNorm)) + "]") 
    #print("Skewness Norm Range: [" + str(numpy.min(skewnessValsNorm)) + ", " + str(numpy.max(skewnessValsNorm)) + "]") 
    
    combined = kurtosisValsNorm + skewnessValsNorm
    #combined = kurtosisValsAbs + skewnessValsAbs
    #print(combined)
    
    minKurt = numpy.unravel_index(numpy.argmin(kurtosisValsAbs, axis=None), kurtosisValsAbs.shape)
    minSkew = numpy.unravel_index(numpy.argmin(skewnessValsAbs, axis=None), skewnessValsAbs.shape)
    minComb = numpy.unravel_index(numpy.argmin(combined, axis=None), combined.shape)
    
    print("Kurtosis bin indexes: ", minKurt)
    print("Skewness bin indexes: ", minSkew)
    print("Combined bin indexes: ", minComb)
    
    lowBinKurt = minKurt[0]
    lowerThresKurt = bin_edges[lowBinKurt] + (binSize/2)
    upBinKurt = numBins-minKurt[1]
    upperThresKurt = bin_edges[upBinKurt] + (binSize/2)
    print("No Change Data Range (Kurtosis): [" + str(lowerThresKurt) + "," + str(upperThresKurt) + "]")
    
    lowBinSkew = minSkew[0]
    lowerThresSkew = bin_edges[lowBinSkew] + (binSize/2)
    upBinSkew = numBins-minSkew[1]
    upperThresSkew = bin_edges[upBinSkew] + (binSize/2)
    print("No Change Data Range (Skewness): [" + str(lowerThresSkew) + "," + str(upperThresSkew) + "]")
        
    lowBinComb = minComb[0]
    lowerThresComb = bin_edges[lowBinComb] + (binSize/2)
    upBinComb = numBins-minComb[1]
    upperThresComb = bin_edges[upBinComb] + (binSize/2)
    print("No Change Data Range (Combined): [" + str(lowerThresComb) + "," + str(upperThresComb) + "]")
    
    lowerThres = 0.0
    upperThres = 0.0
    if thresMeasure == RSGISRATThresMeasure.kurtosis:
        lowerThres = lowerThresKurt
        upperThres = upperThresKurt
    elif thresMeasure == RSGISRATThresMeasure.skewness:
        lowerThres = lowerThresSkew
        upperThres = upperThresSkew
    elif thresMeasure == RSGISRATThresMeasure.combined:
        lowerThres = lowerThresComb
        upperThres = upperThresComb
    elif thresMeasure == RSGISRATThresMeasure.auto:
        if (abs(lowerThresKurt-lowerThresSkew) > (uq-lq)) or (abs(upperThresKurt-upperThresSkew) > (uq-lq)):
            lowerThres = lowerThresSkew
            upperThres = upperThresSkew
        else:
            lowerThres = lowerThresComb
            upperThres = upperThresComb
        print("No Change Data Range (auto): [" + str(lowerThres) + "," + str(upperThres) + "]")
    else:
        raise Exception("Don't understand metric for threshold provided must be of type ThresMeasure")
    

    if not exportPlot == None:
        center = (bin_edges[:-1] + bin_edges[1:]) / 2
        plt.bar(center, hist, align='center', width=binSize)
        if showAllThreshPlot:
            plt.vlines(lowerThresKurt, 0, numpy.max(hist), color='y', linewidth=1, label='Kurtosis Lower')
            plt.vlines(upperThresKurt, 0, numpy.max(hist), color='y', linewidth=1, label='Kurtosis Upper')
            plt.vlines(lowerThresSkew, 0, numpy.max(hist), color='r', linewidth=1, label='Skewness Lower')
            plt.vlines(upperThresSkew, 0, numpy.max(hist), color='r', linewidth=1, label='Skewness Upper')
            plt.vlines(lowerThresComb, 0, numpy.max(hist), color='g', linewidth=1, label='Combined Lower')
            plt.vlines(upperThresComb, 0, numpy.max(hist), color='g', linewidth=1, label='Combined Upper')
        else:
            plt.vlines(lowerThres, 0, numpy.max(hist), color='r', linewidth=1, label='Lower Threshold')
            plt.vlines(upperThres, 0, numpy.max(hist), color='r', linewidth=1, label='Upper Threshold')
        plt.grid(True)
        plt.legend(loc=0)
        plt.savefig(exportPlot)
        plt.close()    
    
    ## Apply to RAT...
    changeFeats = numpy.where(vals < lowerThres, 1, 0)
    changeFeats = numpy.where(vals > upperThres, 2, changeFeats)
    
    outChangeFeats[ID] = changeFeats
    rat.writeColumn(ratDataset, outChangeFeatCol, outChangeFeats)
    
    ratDataset = None
    return [lowerThres, upperThres]
    
def findChangeClumpsHistSkewKurtTestLower(inputClumps, inClassCol, classOfInterest, changeVarCol, outChangeFeatCol, noDataVals=[], thresMeasure=RSGISRATThresMeasure.auto, exportPlot=None, showAllThreshPlot=False):
    """
    This function identifies potential change features from just the lower (left) side of the histogram 
    by slicing the histogram and finding an optimal skewness and kurtosis.
    
    Where:
    
    * inputClumps - input clumps file.
    * inClassCol - The column specifiying the classes, one of which change will be found.
    * classOfInterest - The class (as defined in inClassCol) on which changed is being found.
    * changeVarCol - changeVarCol - Variable(s) to be used to find change. Expecting column name. Needs to be numeric. If a list of column names is provided then they are combined using PCA and the first PC is used for the change process.
    * outChangeFeatCol - the output column. Regions lower than lower threshold have value 1. Regions higher than upper threshold have value 2. No change had threshold 0.
    * noDataVals - list of no data values to be ignored.
    * thresMeasure - needs to be of type RSGISRATThresMeasure (default is auto)
    * exportPlot - file name for exporting a histogram plot with thresholds annotated. No plot is create if None is passed (default is none).
    * showAllThreshPlot - option when plotting to put all the thresholds on to the plot rather than just the one being used.
    
    Return:
    * list of lower [0] and upper [1] thresholds used to define the no change region.
    
    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    # Check scipy stats is available
    if not haveScipyStats:
        raise Exception("The scipy stats is required for this function could not be imported\n\t" + scipystatsErr)
    if not exportPlot == None:
        # Check matplotlib is available
        if not haveMatPlotLib:
            raise Exception("The matplotlib module is required for this function could not be imported\n\t" + pltErr)
    if type(changeVarCol) is list:
        if not haveSKLearnPCA:
            raise Exception("The scikit learn library PCA module is required when a list of column variables is given\n\t" + sklearnPCAErr)
    ## Open the image file...
    ratDataset = gdal.Open(inputClumps, gdal.GA_Update)

    ## Read in columns
    classVals = rat.readColumn(ratDataset, inClassCol)
    outChangeFeats = numpy.zeros_like(classVals)
    ID = numpy.arange(classVals.shape[0])
    
    vals = None
    if type(changeVarCol) is list:
        numVars = len(changeVarCol)
        numRows = classVals.shape[0]
        varVals = numpy.zeros((numVars,numRows), dtype=numpy.float)
        i = 0
        for varCol in changeVarCol:
            colVals = rat.readColumn(ratDataset, varCol)
            varVals[i] = colVals
            i = i + 1
        varVals = varVals.transpose()
        
        ID = ID[classVals == classOfInterest]
        varVals = varVals[(classVals == classOfInterest)]
        
        ID = ID[numpy.isfinite(varVals).all(axis=1)]
        varVals = varVals[numpy.isfinite(varVals).all(axis=1)]
        
        for noDataVal in noDataVals:
            ID = ID[(varVals != noDataVal).all(axis=1)]
            varVals = varVals[(varVals != noDataVal).all(axis=1)]
        
        pca = PCA(n_components=1)
        fittedPCA = pca.fit(varVals)
    
        vals = fittedPCA.transform(varVals)[:,0]
    else:
        vals = rat.readColumn(ratDataset, changeVarCol)        
    
        ID = ID[classVals == classOfInterest]
        if ID.shape[0] == 0:
            rat.writeColumn(ratDataset, outChangeFeatCol, outChangeFeats)
            return
        vals = vals[classVals == classOfInterest]
        
        ID = ID[numpy.isfinite(vals)]
        vals = vals[numpy.isfinite(vals)]
        
        for noDataVal in noDataVals:
            ID = ID[vals != noDataVal]
            vals = vals[vals != noDataVal]

        
    #print(ID)
    #print(vals)
    
    n = vals.shape[0]
    lq = numpy.percentile(vals, 25)
    uq = numpy.percentile(vals, 75)
    iqr = uq - lq
    binSize = 2 * iqr * n**(-1/3)
    print("Bin Size = ", binSize)
    numBins = int((numpy.max(vals) - numpy.min(vals))/binSize)+2
    print("num of bins = ", numBins)
    
    hist, bin_edges = numpy.histogram(vals, bins=numBins)
    
    print(hist.shape)
    print(bin_edges.shape)
        
    print("LQ = ", lq)
    print("UQ = ", uq)
    
    lqNumBins = int((lq - bin_edges[0])/binSize)+1
    
    print("lqNumBins = ", lqNumBins)
    
    kurtosisVals = numpy.zeros((lqNumBins), dtype=numpy.float)
    skewnessVals = numpy.zeros((lqNumBins), dtype=numpy.float)
    lowBins = numpy.zeros((lqNumBins), dtype=numpy.int)
    
    for lowBin in range(lqNumBins):
        #print("Bin [" + str(lowBin) + ", " + str(numBins-upBin) + "]")
        histTmp = hist[lowBin:-1]
        #print(histTmp)
        #print(histTmp.shape)
        lowBins[lowBin] = lowBin
        
        kurtosisVals[lowBin] = scipy.stats.kurtosis(histTmp)
        skewnessVals[lowBin] = scipy.stats.skew(histTmp)
            
    
    #print(kurtosisVals)
    #print(skewnessVals)
    kurtosisValsAbs = numpy.absolute(kurtosisVals)
    skewnessValsAbs = numpy.absolute(skewnessVals)
    print("Kurtosis Range: [" + str(numpy.min(kurtosisValsAbs)) + ", " + str(numpy.max(kurtosisValsAbs)) + "]") 
    print("Skewness Range: [" + str(numpy.min(skewnessValsAbs)) + ", " + str(numpy.max(skewnessValsAbs)) + "]") 
    kurtosisValsNorm = (kurtosisValsAbs-numpy.min(kurtosisValsAbs)) / (numpy.max(kurtosisValsAbs)-numpy.min(kurtosisValsAbs))
    skewnessValsNorm = (skewnessValsAbs-numpy.min(skewnessValsAbs)) / (numpy.max(skewnessValsAbs)-numpy.min(skewnessValsAbs))
    
    #print("Kurtosis Norm Range: [" + str(numpy.min(kurtosisValsNorm)) + ", " + str(numpy.max(kurtosisValsNorm)) + "]") 
    #print("Skewness Norm Range: [" + str(numpy.min(skewnessValsNorm)) + ", " + str(numpy.max(skewnessValsNorm)) + "]") 
    
    combined = kurtosisValsNorm + skewnessValsNorm
    #combined = kurtosisValsAbs + skewnessValsAbs
    #print(combined)
    
    minKurt = numpy.argmin(kurtosisValsAbs)
    minSkew = numpy.argmin(skewnessValsAbs)
    minComb = numpy.argmin(combined)
    
    print("Kurtosis bin index: ", minKurt)
    print("Skewness bin index: ", minSkew)
    print("Combined bin index: ", minComb)
    
    lowBinKurt = minKurt
    lowerThresKurt = bin_edges[lowBinKurt] + (binSize/2)
    print("Lower Threshold (Kurtosis): " + str(lowerThresKurt))
    
    lowBinSkew = minSkew
    lowerThresSkew = bin_edges[lowBinSkew] + (binSize/2)
    print("Lower Threshold (Skewness): " + str(lowerThresSkew))
        
    lowBinComb = minComb
    lowerThresComb = bin_edges[lowBinComb] + (binSize/2)
    print("Lower Threshold (Combined): " + str(lowerThresComb))
    
    lowerThres = 0.0
    upperThres = numpy.max(vals)
    if thresMeasure == RSGISRATThresMeasure.kurtosis:
        lowerThres = lowerThresKurt
    elif thresMeasure == RSGISRATThresMeasure.skewness:
        lowerThres = lowerThresSkew
    elif thresMeasure == RSGISRATThresMeasure.combined:
        lowerThres = lowerThresComb
    elif thresMeasure == RSGISRATThresMeasure.auto:
        if abs(lowerThresKurt-lowerThresSkew) > (uq-lq):
            lowerThres = lowerThresSkew
        else:
            lowerThres = lowerThresComb        
        print("Lower Threshold (auto): " + str(lowerThres))
    else:
        raise Exception("Don't understand metric for threshold provided must be of type ThresMeasure")
    
    if not exportPlot == None:
        center = (bin_edges[:-1] + bin_edges[1:]) / 2
        plt.bar(center, hist, align='center', width=binSize)
        if showAllThreshPlot:
            plt.vlines(lowerThresKurt, 0, numpy.max(hist), color='y', linewidth=1, label='Kurtosis Lower')
            plt.vlines(lowerThresSkew, 0, numpy.max(hist), color='r', linewidth=1, label='Skewness Lower')
            plt.vlines(lowerThresComb, 0, numpy.max(hist), color='g', linewidth=1, label='Combined Lower')
        else:
            plt.vlines(lowerThres, 0, numpy.max(hist), color='r', linewidth=1, label='Lower Threshold')
        plt.grid(True)
        plt.legend(loc=0)
        plt.savefig(exportPlot)
        plt.close()
    
    ## Apply to RAT...
    changeFeats = numpy.where(vals < lowerThres, 1, 0)
    
    outChangeFeats[ID] = changeFeats
    rat.writeColumn(ratDataset, outChangeFeatCol, outChangeFeats)
    
    ratDataset = None
    return [lowerThres, upperThres]


def findChangeClumpsHistSkewKurtTestUpper(inputClumps, inClassCol, classOfInterest, changeVarCol, outChangeFeatCol, noDataVals=[], thresMeasure=RSGISRATThresMeasure.auto, exportPlot=None, showAllThreshPlot=False):
    """
    This function identifies potential change features from just the upper (right) side of the histogram 
    by slicing the histogram and finding an optimal skewness and kurtosis.
    
    Where:
    
    * inputClumps - input clumps file.
    * inClassCol - The column specifiying the classes, one of which change will be found.
    * classOfInterest - The class (as defined in inClassCol) on which changed is being found.
    * changeVarCol - changeVarCol - Variable(s) to be used to find change. Expecting column name. Needs to be numeric. If a list of column names is provided then they are combined using PCA and the first PC is used for the change process.
    * outChangeFeatCol - the output column. Regions lower than lower threshold have value 1. Regions higher than upper threshold have value 2. No change had threshold 0.
    * noDataVals - list of no data values to be ignored.
    * thresMeasure - needs to be of type RSGISRATThresMeasure (default is auto)
    * exportPlot - file name for exporting a histogram plot with thresholds annotated. No plot is create if None is passed (default is none).
    * showAllThreshPlot - option when plotting to put all the thresholds on to the plot rather than just the one being used.
    
    Return:
    * list of lower [0] and upper [1] thresholds used to define the no change region.
    
    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    # Check scipy stats is available
    if not haveScipyStats:
        raise Exception("The scipy stats is required for this function could not be imported\n\t" + scipystatsErr)
    if not exportPlot == None:
        # Check matplotlib is available
        if not haveMatPlotLib:
            raise Exception("The matplotlib module is required for this function could not be imported\n\t" + pltErr)
    if type(changeVarCol) is list:
        if not haveSKLearnPCA:
            raise Exception("The scikit learn library PCA module is required when a list of column variables is given\n\t" + sklearnPCAErr)
    ## Open the image file...
    ratDataset = gdal.Open(inputClumps, gdal.GA_Update)

    ## Read in columns
    classVals = rat.readColumn(ratDataset, inClassCol)
    outChangeFeats = numpy.zeros_like(classVals)
    ID = numpy.arange(classVals.shape[0])
    
    vals = None
    if type(changeVarCol) is list:
        numVars = len(changeVarCol)
        numRows = classVals.shape[0]
        varVals = numpy.zeros((numVars,numRows), dtype=numpy.float)
        i = 0
        for varCol in changeVarCol:
            colVals = rat.readColumn(ratDataset, varCol)
            varVals[i] = colVals
            i = i + 1
        varVals = varVals.transpose()
        
        ID = ID[classVals == classOfInterest]
        varVals = varVals[(classVals == classOfInterest)]
        
        ID = ID[numpy.isfinite(varVals).all(axis=1)]
        varVals = varVals[numpy.isfinite(varVals).all(axis=1)]
        
        for noDataVal in noDataVals:
            ID = ID[(varVals != noDataVal).all(axis=1)]
            varVals = varVals[(varVals != noDataVal).all(axis=1)]
        
        pca = PCA(n_components=1)
        fittedPCA = pca.fit(varVals)
    
        vals = fittedPCA.transform(varVals)[:,0]
    else:
        vals = rat.readColumn(ratDataset, changeVarCol)        
    
        ID = ID[classVals == classOfInterest]
        if ID.shape[0] == 0:
            rat.writeColumn(ratDataset, outChangeFeatCol, outChangeFeats)
            return
        vals = vals[classVals == classOfInterest]
        
        ID = ID[numpy.isfinite(vals)]
        vals = vals[numpy.isfinite(vals)]
        
        for noDataVal in noDataVals:
            ID = ID[vals != noDataVal]
            vals = vals[vals != noDataVal]
        
    #print(ID)
    #print(vals)
    
    n = vals.shape[0]
    lq = numpy.percentile(vals, 25)
    uq = numpy.percentile(vals, 75)
    iqr = uq - lq
    binSize = 2 * iqr * n**(-1/3)
    print("Bin Size = ", binSize)
    numBins = int((numpy.max(vals) - numpy.min(vals))/binSize)+2
    print("num of bins = ", numBins)
    
    hist, bin_edges = numpy.histogram(vals, bins=numBins)
    
    print(hist.shape)
    print(bin_edges.shape)
        
    print("LQ = ", lq)
    print("UQ = ", uq)
    
    uqNumBins = int((bin_edges[-1]-uq)/binSize)+1
    
    print("uqNumBins = ", uqNumBins)
    
    kurtosisVals = numpy.zeros((uqNumBins), dtype=numpy.float)
    skewnessVals = numpy.zeros((uqNumBins), dtype=numpy.float)
    upBins = numpy.zeros((uqNumBins), dtype=numpy.int)
    
    for upBin in range(uqNumBins):
        #print("Bin [" + str(lowBin) + ", " + str(numBins-upBin) + "]")
        histTmp = hist[0:(numBins-upBin)]
        #print(histTmp)
        #print(histTmp.shape)
        upBins[upBin] = numBins-upBin
        
        kurtosisVals[upBin] = scipy.stats.kurtosis(histTmp)
        skewnessVals[upBin] = scipy.stats.skew(histTmp)
        
    
    #print(kurtosisVals)
    #print(skewnessVals)
    kurtosisValsAbs = numpy.absolute(kurtosisVals)
    skewnessValsAbs = numpy.absolute(skewnessVals)
    print("Kurtosis Range: [" + str(numpy.min(kurtosisValsAbs)) + ", " + str(numpy.max(kurtosisValsAbs)) + "]") 
    print("Skewness Range: [" + str(numpy.min(skewnessValsAbs)) + ", " + str(numpy.max(skewnessValsAbs)) + "]") 
    kurtosisValsNorm = (kurtosisValsAbs-numpy.min(kurtosisValsAbs)) / (numpy.max(kurtosisValsAbs)-numpy.min(kurtosisValsAbs))
    skewnessValsNorm = (skewnessValsAbs-numpy.min(skewnessValsAbs)) / (numpy.max(skewnessValsAbs)-numpy.min(skewnessValsAbs))
    
    #print("Kurtosis Norm Range: [" + str(numpy.min(kurtosisValsNorm)) + ", " + str(numpy.max(kurtosisValsNorm)) + "]") 
    #print("Skewness Norm Range: [" + str(numpy.min(skewnessValsNorm)) + ", " + str(numpy.max(skewnessValsNorm)) + "]") 
    
    combined = kurtosisValsNorm + skewnessValsNorm
    #combined = kurtosisValsAbs + skewnessValsAbs
    #print(combined)
    
    minKurt = numpy.argmin(kurtosisValsAbs)
    minSkew = numpy.argmin(skewnessValsAbs)
    minComb = numpy.argmin(combined)
    
    print("Kurtosis bin index: ", minKurt)
    print("Skewness bin index: ", minSkew)
    print("Combined bin index: ", minComb)
    
    upBinKurt = numBins-minKurt
    upperThresKurt = bin_edges[upBinKurt] + (binSize/2)
    print("Upper Threshold (Kurtosis): " + str(upperThresKurt))
    
    upBinSkew = numBins-minSkew
    upperThresSkew = bin_edges[upBinSkew] + (binSize/2)
    print("Upper Threshold (Skewness): " + str(upperThresSkew))
        
    upBinComb = numBins-minComb
    upperThresComb = bin_edges[upBinComb] + (binSize/2)
    print("Upper Threshold (Combined): " + str(upperThresComb))
    
    lowerThres = numpy.min(vals)
    upperThres = 0.0
    if thresMeasure == RSGISRATThresMeasure.kurtosis:
        upperThres = upperThresKurt
    elif thresMeasure == RSGISRATThresMeasure.skewness:
        upperThres = upperThresSkew
    elif thresMeasure == RSGISRATThresMeasure.combined:
        upperThres = upperThresComb
    elif thresMeasure == RSGISRATThresMeasure.auto:
        if abs(upperThresKurt-upperThresSkew) > (uq-lq):
            upperThres = upperThresSkew
        else:
            upperThres = upperThresComb
        print("Upper Threshold (auto): " + str(upperThres))
    else:
        raise Exception("Don't understand metric for threshold provided must be of type ThresMeasure")
    
    if not exportPlot == None:
        center = (bin_edges[:-1] + bin_edges[1:]) / 2
        plt.bar(center, hist, align='center', width=binSize)
        if showAllThreshPlot:
            plt.vlines(upperThresKurt, 0, numpy.max(hist), color='y', linewidth=1, label='Kurtosis Upper')
            plt.vlines(upperThresSkew, 0, numpy.max(hist), color='r', linewidth=1, label='Skewness Upper')
            plt.vlines(upperThresComb, 0, numpy.max(hist), color='g', linewidth=1, label='Combined Upper')
        else:
            plt.vlines(upperThres, 0, numpy.max(hist), color='r', linewidth=1, label='Upper Threshold')
        plt.grid(True)
        plt.legend(loc=0)
        plt.savefig(exportPlot)
        plt.close()
        
    ## Apply to RAT...
    changeFeats = numpy.where(vals > upperThres, 1, 0)
    
    outChangeFeats[ID] = changeFeats
    rat.writeColumn(ratDataset, outChangeFeatCol, outChangeFeats)
    
    ratDataset = None
    return [lowerThres, upperThres]


class RSGISRATChangeVarInfo:
    """
    A class to store the change variable information required for some of the change functions.
    """
    def __init__(self, changeVarCol="", outChangeFeatCol="", noDataVals=[], thresMeasure=RSGISRATThresMeasure.auto, thresDirection=RSGISRATThresDirection.lower, exportPlot=None, showAllThreshPlot=False, lowerThreshold=0.0, upperThreshold=0.0):
        self.changeVarCol = changeVarCol
        self.outChangeFeatCol = outChangeFeatCol
        self.noDataVals = noDataVals
        self.thresMeasure = thresMeasure
        self.thresDirection = thresDirection
        self.exportPlot = exportPlot
        self.showAllThreshPlot = showAllThreshPlot
        self.lowerThreshold = lowerThreshold
        self.upperThreshold = upperThreshold

def findChangeClumpsHistSkewKurtTestVoteMultiVars(inputClumps, inClassCol, classOfInterest, outChangeFeatCol, vars=[]):
    """
    A function to call one of the findChangeClumpsHistSkewKurtTest functions for multiple 
    variables and then combine together by voting to find change features.
    
    Where:
    * inputClumps - input clumps file.
    * inClassCol - The column specifiying the classes, one of which change will be found.
    * classOfInterest - The class (as defined in inClassCol) on which changed is being found.
    * outChangeFeatCol - the output column with the vote scores.
    * vars - a list of RSGISRATChangeVarInfo objects used to specify the variables and function to be called.
    
    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    if len(vars) == 0:
        raise Exception("Need to provide a list of variables with parameters...")
    for var in vars:
        print(var.changeVarCol)
        if var.thresDirection == RSGISRATThresDirection.lower:
            outThres = findChangeClumpsHistSkewKurtTestLower(inputClumps, inClassCol, classOfInterest, var.changeVarCol, var.outChangeFeatCol, var.noDataVals, var.thresMeasure, var.exportPlot, var.showAllThreshPlot)
            var.lowerThreshold = outThres[0]
            var.upperThreshold = outThres[1]
        elif var.thresDirection == RSGISRATThresDirection.upper:
            outThres = findChangeClumpsHistSkewKurtTestUpper(inputClumps, inClassCol, classOfInterest, var.changeVarCol, var.outChangeFeatCol, var.noDataVals, var.thresMeasure, var.exportPlot, var.showAllThreshPlot)
            var.lowerThreshold = outThres[0]
            var.upperThreshold = outThres[1]
        elif var.thresDirection == RSGISRATThresDirection.lowerupper:
            outThres = findChangeClumpsHistSkewKurtTest(inputClumps, inClassCol, classOfInterest, var.changeVarCol, var.outChangeFeatCol, var.noDataVals, var.thresMeasure, var.exportPlot, var.showAllThreshPlot)
            var.lowerThreshold = outThres[0]
            var.upperThreshold = outThres[1]
        else:
            raise Exception("Direction must be of type RSGISRATThresDirection and only lower, upper and lowerupper are supported")
        
    ratDataset = gdal.Open(inputClumps, gdal.GA_Update)
    classVals = rat.readColumn(ratDataset, inClassCol)
    changeVote = numpy.zeros_like(classVals, dtype=numpy.int)

    for var in vars:
        changeCol = rat.readColumn(ratDataset, var.outChangeFeatCol)
        if var.thresDirection == RSGISRATThresDirection.lowerupper:
            changeCol[changeCol == 2] = 1
        changeVote = changeVote + changeCol
    
    rat.writeColumn(ratDataset, outChangeFeatCol, changeVote)
    ratDataset = None

def findClumpsWithinExistingThresholds(inputClumps, inClassCol, classOfInterest, outFeatsCol, vars=[]):
    """
    A function to use the thresholds stored in the RSGISRATChangeVarInfo objects (var) 
    and populated from the findChangeClumpsHistSkewKurtTest functions to assess another class
    creating a binary column as to whether a feature is within the threshold or now. Where multiple
    variables (i.e., len(var) > 1) then variables are combined with an and operation.
    
    Where:
    * inputClumps - input clumps file.
    * inClassCol - The column specifiying the classes, one of which change will be found.
    * classOfInterest - The class (as defined in inClassCol) on which changed is being found.
    * outFeatsCol - the output binary column specifying whether a feature is within the thresholds.
    * vars - a list of RSGISRATChangeVarInfo objects used to specify the variables and function to be called.
    
    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    if len(vars) == 0:
        raise Exception("Need to provide a list of variables with parameters...")
        
    ## Open the image file...
    ratDataset = gdal.Open(inputClumps, gdal.GA_Update)

    ## Read in columns
    classVals = rat.readColumn(ratDataset, inClassCol)
    outFeats = numpy.zeros_like(classVals)
    
    first = True
    for var in vars:
        print(var.changeVarCol)
        if first:
            varVals = rat.readColumn(ratDataset, var.changeVarCol)
            outFeats = numpy.where( (varVals > var.lowerThreshold) & (varVals < var.upperThreshold) & (classVals == classOfInterest), 1, outFeats)
            first = False
        else:
            varVals = rat.readColumn(ratDataset, var.changeVarCol)
            outFeats = numpy.where( (varVals > var.lowerThreshold) & (varVals < var.upperThreshold) & (classVals == classOfInterest), outFeats, 0)
        
    rat.writeColumn(ratDataset, outFeatsCol, outFeats)
    ratDataset = None


def _ratapplier_defClassNames(info, inputs, outputs, otherargs):
    classNum = getattr(inputs.inrat, otherargs.classNumCol)
    
    classNames = numpy.empty_like(classNum, dtype=numpy.dtype('a255'))
    classNames[...] = ''
    
    for key in otherargs.classNamesDict:
        classNames = numpy.where((classNum == key), otherargs.classNamesDict[key], classNames)

    setattr(outputs.outrat, otherargs.classNameCol, classNames)

def defineClassNames(clumps, classNumCol, classNameCol, classNamesDict):
    in_rats = ratapplier.RatAssociations()
    out_rats = ratapplier.RatAssociations()
                
    in_rats.inrat = ratapplier.RatHandle(clumps)
    out_rats.outrat = ratapplier.RatHandle(clumps)

    otherargs = ratapplier.OtherArguments()
    otherargs.classNumCol = classNumCol
    otherargs.classNameCol = classNameCol
    otherargs.classNamesDict = classNamesDict

    ratapplier.apply(_ratapplier_defClassNames, in_rats, out_rats, otherargs)


def populateClumpsWithClassTraining(clumpsImg, classesDict, tmpPath, classesIntCol, classesNameCol):
    """
    A function to populate a clumps file with training from a series of shapefiles (1 per class)
    
    Where:
    * clumpsImg - input clumps file.
    * classesDict - A dict structure with the class names as keys and the values are an array of two values [int class val, file path for shapefile].
    * tmpPath - File path (which needs to exist) where files can temporally be written.
    * classesIntCol - Output column name for integer values representing each class.
    * classesNameCol - Output column name for string class names.
    
    """
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    
    createdDIR = False
    if not os.path.isdir(tmpPath):
        os.makedirs(tmpPath)
        createdDIR = True
    
    rsPyUtils = rsgislib.RSGISPyUtils()
    uid = rsPyUtils.uidGenerator(10)
    
    classLayerSeq = list()
    tmpClassImgLayers = list()
    classNamesDict = dict()
    
    for key in classesDict:
        className = key
        classShpFile = classesDict[key][1]
        classImgFile = os.path.join(tmpPath, className+"_"+uid+".kea")
        classIntVal = classesDict[key][0]
        vectorutils.rasterise2Image(classShpFile, clumpsImg, classImgFile, gdalFormat="KEA", burnVal=classIntVal)
        tmpClassImgLayers.append(classImgFile)
        classNamesDict[classIntVal] = className
    
    combinedClassesImage = os.path.join(tmpPath, "CombinedClasses_" + uid + ".kea")
    imageutils.combineImages2Band(tmpClassImgLayers, combinedClassesImage, 'KEA', rsgislib.TYPE_8UINT, 0.0)
    
    rastergis.populateRATWithMode(valsimage=combinedClassesImage, clumps=clumpsImg, outcolsname=classesIntCol, usenodata=False, nodataval=0, modeband=1, ratband=1)
    defineClassNames(clumpsImg, classesIntCol, classesNameCol, classNamesDict)
    
    for file in tmpClassImgLayers:
        rsPyUtils.deleteFileWithBasename(file)
    rsPyUtils.deleteFileWithBasename(combinedClassesImage)
    
    if createdDIR:
        shutil.rmtree(tmpPath)
    


def createClumpsSHPBBOX(clumpsImg, minXCol, maxXCol, minYCol, maxYCol, outShpLyrName, roundInt=False):
    """
    A function to create a shapefile of polygons with the bboxs of the clumps defined using 
    the minX, maxX, minY and maxY coordinates for the features.
    
    Where:
    * clumpsImg - input clumps file.
    * minXCol - the minX column in RAT.
    * maxXCol - the maxX column in RAT.
    * minYCol - the minY column in RAT.
    * maxYCol - the maxY column in RAT.
    * outShpLyrName - The output shapefile name (layer name do not include the .shp it will be appended).
    * roundInt - Boolean specifying whether the coordinated should be rounded to integers (Default: False)
    
    """   
    
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    # Check gdal ogr is available
    if not haveGDALOGRPy:
        raise Exception("The GDAL OGR python bindings are required for this function could not be imported\n\t" + gdalogrErr)
    
    ratDataset = gdal.Open(clumpsImg)

    minXVals = rat.readColumn(ratDataset, minXCol)
    maxXVals = rat.readColumn(ratDataset, maxXCol)
    minYVals = rat.readColumn(ratDataset, minYCol)
    maxYVals = rat.readColumn(ratDataset, maxYCol)
    
    fidVals = numpy.arange(minXCol.shape[0])

    ## Remove First Row which is no data...    
    dataMask = numpy.ones_like(minXVals, dtype=numpy.int16)
    dataMask[0] = 0
    minXVals = minXVals[dataMask == 1]
    maxXVals = maxXVals[dataMask == 1]
    minYVals = minYVals[dataMask == 1]
    maxYVals = maxYVals[dataMask == 1]
    fidVals = fidVals[dataMask == 1]
    
    ## Remove any features which are all zero (i.e., polygon not present...
    minXValsSub = minXVals[numpy.logical_not((minXVals == 0) & (maxXVals == 0) & (minYVals == 0) & (maxYVals == 0))]
    maxXValsSub = maxXVals[numpy.logical_not((minXVals == 0) & (maxXVals == 0) & (minYVals == 0) & (maxYVals == 0))]
    minYValsSub = minYVals[numpy.logical_not((minXVals == 0) & (maxXVals == 0) & (minYVals == 0) & (maxYVals == 0))]
    maxYValsSub = maxYVals[numpy.logical_not((minXVals == 0) & (maxXVals == 0) & (minYVals == 0) & (maxYVals == 0))]
    fidValsSub = fidVals[numpy.logical_not((minXVals == 0) & (maxXVals == 0) & (minYVals == 0) & (maxYVals == 0))]

    if roundInt:
        minXValsSub = numpy.rint(minXValsSub)
        maxXValsSub = numpy.rint(maxXValsSub)
        minYValsSub = numpy.rint(minYValsSub)
        maxYValsSub = numpy.rint(maxYValsSub)
    
    numFeats = minXValsSub.shape[0]
    print("Num Feats: ", numFeats)
    
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(outShpLyrName+".shp"):
        driver.DeleteDataSource(outShpLyrName+".shp")
    outDatasource = driver.CreateDataSource(outShpLyrName+ ".shp")
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromWkt(ratDataset.GetProjectionRef())
    outLayer = outDatasource.CreateLayer(outShpLyrName, srs=raster_srs)
    
    fieldFIDDefn = ogr.FieldDefn('ID', ogr.OFTInteger) 
    fieldFIDDefn.SetWidth(6) 
    outLayer.CreateField(fieldFIDDefn)
    
    print("Create and Add Polygons...")
    for i in range(numFeats):
        wktStr = "POLYGON((" + str(minXValsSub[i]) + " " + str(maxYValsSub[i]) + ", " + str(maxXValsSub[i]) + " " + str(maxYValsSub[i]) + ", " + str(maxXValsSub[i]) + " " + str(minYValsSub[i]) + ", " + str(minXValsSub[i]) + " " + str(minYValsSub[i]) + ", " + str(minXValsSub[i]) + " " + str(maxYValsSub[i]) + "))"
        #print(str(i) + ": " + wktStr)
        poly = ogr.CreateGeometryFromWkt(wktStr)
        feat = ogr.Feature( outLayer.GetLayerDefn())
        feat.SetGeometry(poly)
        feat.SetField("ID", fidValsSub[i])
        if outLayer.CreateFeature(feat) != 0:
            print(str(i) + ": " + wktStr)
            print("Failed to create feature in shapefile.\n")
            sys.exit( 1 )
        feat.Destroy()
        
    outDatasource.Destroy()
    ratDataset = None
    print("Completed")


def identifySmallUnits(clumpsImg, classCol, tmpPath, outColName, smallClumpsThres):
    """
Identify small connected units within a classification. The threshold to define small
is provided by the user in pixels. Note, the outColName and smallClumpsThres variables
can be provided as lists to identify a number of thresholds of small units.

* clumpsImg - string for the clumps image file containing input classification
* classCol - string for the column name representing the classification as integer values
* tmpPath - directory path for 
* outColName
* smallClumpsThres

Example::
from rsgislib.rastergis import ratutils

clumpsImg = "LS2MSS_19750620_lat10lon6493_r67p250_rad_srefdem_30m_clumps.kea"
tmpPath = "./tmp/"
classCol = "OutClass"
outColName = ["SmallUnits25", "SmallUnits50", "SmallUnits100"]
smallClumpsThres = [25, 50, 100]
rastergis.identifySmallUnits(clumpsImg, classCol, tmpPath, outColName, smallClumpsThres)

    """
    
    # Check numpy is available
    if not haveNumpy:
        raise Exception("The numpy module is required for this function could not be imported\n\t" + numErr)
    # Check gdal is available
    if not haveGDALPy:
        raise Exception("The GDAL python bindings are required for this function could not be imported\n\t" + gdalErr)
    # Check rios rat is available
    if not haveRIOSRat:
        raise Exception("The RIOS rat tools are required for this function could not be imported\n\t" + riosRatErr)
    
    if len(outColName) is not len(smallClumpsThres):
        print("The number of threshold values and output column names should be the same.")
        sys.exit(-1)
    
    numThresholds = len(smallClumpsThres)
        
    createdDIR = False
    if not os.path.isdir(tmpPath):
        os.makedirs(tmpPath)
        createdDIR = True
        
    
    baseName = os.path.splitext(os.path.basename(clumpsImg))[0]
    classMaskImg = os.path.join(tmpPath, baseName+"_TmpClassMask.kea")
    classMaskClumps = os.path.join(tmpPath, baseName+"_TmpClassMaskClumps.kea")
    smallClumpsMask = os.path.join(tmpPath, baseName+"_SmallClassClumps.kea")
    
    rastergis.exportCol2GDALImage(clumpsImg, classMaskImg, "KEA", rsgislib.TYPE_16UINT, classCol)
    segmentation.clump(classMaskImg, classMaskClumps, "KEA", False, 0)
    rastergis.populateStats(classMaskClumps, False, False)
        
    for i in range(numThresholds):
        print("Processing thresold " + str(smallClumpsThres[i]) + " - " + outColName[i])
        ratDataset = gdal.Open(classMaskClumps, gdal.GA_Update)
        Histogram = rat.readColumn(ratDataset, "Histogram")
        smallUnits = numpy.zeros_like(Histogram, dtype=numpy.int16)
        smallUnits[Histogram < smallClumpsThres[i]] = 1
        rat.writeColumn(ratDataset, "smallUnits", smallUnits)
        ratDataset = None
    
        rastergis.exportCol2GDALImage(classMaskClumps, smallClumpsMask, "KEA", rsgislib.TYPE_8UINT, "smallUnits")
    
        bs = []
        bs.append(rastergis.BandAttStats(band=1, maxField=outColName[i]))
        rastergis.populateRATWithStats(smallClumpsMask, clumpsImg, bs)
    
    rsgisUtils = rsgislib.RSGISPyUtils()
    rsgisUtils.deleteFileWithBasename(classMaskImg)
    rsgisUtils.deleteFileWithBasename(classMaskClumps)
    rsgisUtils.deleteFileWithBasename(smallClumpsMask)
    if createdDIR:
        shutil.rmtree(tmpPath)





