/*
 *  RSGISCmdHistoCube.cpp
 *
 *
 *  Created by Pete Bunting on 17/02/2017.
 *  Copyright 2017 RSGISLib.
 *
 *  RSGISLib is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  RSGISLib is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with RSGISLib.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "RSGISCmdHistoCube.h"
#include "RSGISCmdParent.h"

#include "common/RSGISHistoCubeException.h"
#include "histocube/RSGISHistoCubeFileIO.h"
#include "histocube/RSGISPopulateHistoCube.h"
#include "histocube/RSGISExportHistoCube2Img.h"

#include "img/RSGISCalcImage.h"
#include "img/RSGISImageStatistics.h"

#include "math/RSGISMathsUtils.h"

namespace rsgis{ namespace cmds {
    
    
    
    void executeCreateEmptyHistoCube(std::string histCubeFile, unsigned long numFeats)
    {
        try
        {
            rsgis::histocube::RSGISHistoCubeFile histoCubeFileObj = rsgis::histocube::RSGISHistoCubeFile();
            histoCubeFileObj.createNewFile(histCubeFile, numFeats);
            histoCubeFileObj.closeFile();
        }
        catch(rsgis::RSGISHistoCubeException &e)
        {
            throw RSGISCmdException(e.what());
        }
    }
    
    void executeCreateHistoCubeLayer(std::string histCubeFile, std::string layerName, int lowBin, int upBin, float scale, float offset, bool hasDateTime, std::string dataTime)
    {
        try
        {
            if(lowBin >= upBin)
            {
                rsgis::RSGISHistoCubeException("The upper bin must be greater than the lower bin.");
            }
            rsgis::histocube::RSGISHistoCubeFile histoCubeFileObj = rsgis::histocube::RSGISHistoCubeFile();
            histoCubeFileObj.openFile(histCubeFile, true);
            
            std::vector<int> bins = std::vector<int>();
            for(int i = lowBin; i <= upBin; ++i)
            {
                bins.push_back(i);
            }
            
            boost::posix_time::ptime *layerDateTime = NULL;
            if(hasDateTime)
            {
                layerDateTime = new boost::posix_time::ptime(boost::posix_time::time_from_string(dataTime));
            }
            
            histoCubeFileObj.createDataset(layerName, bins, scale, offset, hasDateTime, layerDateTime);
            histoCubeFileObj.closeFile();
        }
        catch(rsgis::RSGISHistoCubeException &e)
        {
            throw RSGISCmdException(e.what());
        }
    }
    
    void executePopulateSingleHistoCubeLayer(std::string histCubeFile, std::string layerName, std::string clumpsImg, std::string valsImg, unsigned int imgBand, bool inMem)
    {
        GDALAllRegister();
        try
        {
            if(imgBand == 0)
            {
                throw rsgis::RSGISImageException("The band specified is not within the values image.");
            }
            
            rsgis::histocube::RSGISHistoCubeFile histoCubeFileObj = rsgis::histocube::RSGISHistoCubeFile();
            histoCubeFileObj.openFile(histCubeFile, true);
            
            std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*> *cubeLayers = histoCubeFileObj.getCubeLayersList();
            rsgis::histocube::RSGISHistCubeLayerMeta *cubeLayer = NULL;
            bool found = false;
            for(std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*>::iterator iterLayers = cubeLayers->begin(); iterLayers != cubeLayers->end(); ++iterLayers)
            {
                if((*iterLayers)->name == layerName)
                {
                    cubeLayer = (*iterLayers);
                    found = true;
                    break;
                }
            }
            
            if(!found)
            {
                throw rsgis::RSGISHistoCubeException("Column was not found within the histogram cube.");
            }
            
            GDALDataset **datasets = new GDALDataset*[2];
            
            datasets[0] = (GDALDataset *) GDALOpen(clumpsImg.c_str(), GA_ReadOnly);
            if(datasets[0] == NULL)
            {
                std::string message = std::string("Could not open image ") + clumpsImg;
                throw rsgis::RSGISImageException(message.c_str());
            }
            
            if(datasets[0]->GetRasterCount() != 1)
            {
                GDALClose(datasets[0]);
                delete[] datasets;
                throw rsgis::RSGISImageException("The clumps image must only have 1 image band.");
            }
            
            datasets[1] = (GDALDataset *) GDALOpen(valsImg.c_str(), GA_ReadOnly);
            if(datasets[1] == NULL)
            {
                std::string message = std::string("Could not open image ") + valsImg;
                throw rsgis::RSGISImageException(message.c_str());
            }
            
            if(imgBand > datasets[1]->GetRasterCount())
            {
                GDALClose(datasets[1]);
                delete[] datasets;
                throw rsgis::RSGISImageException("The band specified is not within the values image.");
            }
            
            unsigned int bandIdx = imgBand-1;
            unsigned int maxRow = histoCubeFileObj.getNumFeatures()-1;
            
            if(inMem)
            {
                unsigned int nBins = cubeLayer->bins.size();
                unsigned long dataArrLen = (maxRow*nBins)+nBins;
                unsigned int *dataArr = new unsigned int[dataArrLen];
                histoCubeFileObj.getHistoRows(layerName, 0, maxRow, dataArr, dataArrLen);
                
                rsgis::histocube::RSGISPopHistoCubeLayerFromImgBandInMem popCubeLyrMem = rsgis::histocube::RSGISPopHistoCubeLayerFromImgBandInMem(dataArr, dataArrLen, bandIdx, maxRow, cubeLayer->scale, cubeLayer->offset, cubeLayer->bins);
                rsgis::img::RSGISCalcImage calcImgPopCubeMem = rsgis::img::RSGISCalcImage(&popCubeLyrMem);
                calcImgPopCubeMem.calcImage(datasets, 1, 1);
                
                histoCubeFileObj.setHistoRows(layerName, 0, maxRow, dataArr, dataArrLen);
                delete[] dataArr;
            }
            else
            {
                rsgis::histocube::RSGISPopHistoCubeLayerFromImgBand popCubeLyr = rsgis::histocube::RSGISPopHistoCubeLayerFromImgBand(&histoCubeFileObj, layerName, bandIdx, maxRow, cubeLayer->scale, cubeLayer->offset, cubeLayer->bins);
                rsgis::img::RSGISCalcImage calcImgPopCube = rsgis::img::RSGISCalcImage(&popCubeLyr);
                calcImgPopCube.calcImage(datasets, 1, 1);
            }
            histoCubeFileObj.closeFile();
            GDALClose(datasets[0]);
            GDALClose(datasets[1]);
            delete[] datasets;
        }
        catch(rsgis::RSGISImageException &e)
        {
            throw RSGISCmdException(e.what());
        }
        catch(rsgis::RSGISHistoCubeException &e)
        {
            throw RSGISCmdException(e.what());
        }
    }
    
    void executeExportHistBins2Img(std::string histCubeFile, std::string layerName, std::string clumpsImg, std::string outputImg, std::string gdalFormat, std::vector<unsigned int> exportBins) 
    {
        GDALAllRegister();
        try
        {
            rsgis::histocube::RSGISHistoCubeFile histoCubeFileObj = rsgis::histocube::RSGISHistoCubeFile();
            histoCubeFileObj.openFile(histCubeFile, true);
            
            std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*> *cubeLayers = histoCubeFileObj.getCubeLayersList();
            rsgis::histocube::RSGISHistCubeLayerMeta *cubeLayer = NULL;
            bool found = false;
            for(std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*>::iterator iterLayers = cubeLayers->begin(); iterLayers != cubeLayers->end(); ++iterLayers)
            {
                if((*iterLayers)->name == layerName)
                {
                    cubeLayer = (*iterLayers);
                    found = true;
                    break;
                }
            }
            
            if(!found)
            {
                throw rsgis::RSGISHistoCubeException("Column was not found within the histogram cube.");
            }
            
            GDALDataset *dataset = (GDALDataset *) GDALOpen(clumpsImg.c_str(), GA_ReadOnly);
            if(dataset == NULL)
            {
                std::string message = std::string("Could not open image ") + clumpsImg;
                throw rsgis::RSGISImageException(message.c_str());
            }
            
            if(dataset->GetRasterCount() != 1)
            {
                GDALClose(dataset);
                throw rsgis::RSGISImageException("The clumps image must only have 1 image band.");
            }
            
            unsigned int maxRow = histoCubeFileObj.getNumFeatures()-1;
            unsigned int nBins = cubeLayer->bins.size();
            unsigned long dataArrLen = (maxRow*nBins)+nBins;
            unsigned int *dataArr = new unsigned int[dataArrLen];
            histoCubeFileObj.getHistoRows(layerName, 0, maxRow, dataArr, dataArrLen);
            
            rsgis::histocube::RSGISExportBins2ImgBands expBins2Img = rsgis::histocube::RSGISExportBins2ImgBands(exportBins.size(), dataArr, dataArrLen, nBins, exportBins);
            rsgis::img::RSGISCalcImage calcImg = rsgis::img::RSGISCalcImage(&expBins2Img);
            calcImg.calcImage(&dataset, 1, 0, outputImg, false, NULL, gdalFormat, GDT_UInt32);
            
            delete[] dataArr;
            GDALClose(dataset);
        }
        catch(rsgis::RSGISImageException &e)
        {
            throw RSGISCmdException(e.what());
        }
        catch(rsgis::RSGISHistoCubeException &e)
        {
            throw RSGISCmdException(e.what());
        }
    }
    
    std::vector<std::string> executeExportHistBins2Img(std::string histCubeFile)
    {
        std::vector<std::string> lyrNames;
        try
        {
            rsgis::histocube::RSGISHistoCubeFile histoCubeFileObj = rsgis::histocube::RSGISHistoCubeFile();
            histoCubeFileObj.openFile(histCubeFile, true);
            
            std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*> *cubeLayers = histoCubeFileObj.getCubeLayersList();
            for(std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*>::iterator iterLayers = cubeLayers->begin(); iterLayers != cubeLayers->end(); ++iterLayers)
            {
                lyrNames.push_back((*iterLayers)->name);
            }
            
            histoCubeFileObj.closeFile();
        }
        catch(rsgis::RSGISHistoCubeException &e)
        {
            throw RSGISCmdException(e.what());
        }
        return lyrNames;
    }
    
    void executeExportHistStats2Img(std::string histCubeFile, std::string layerName, std::string clumpsImg, std::string outputImg, std::string gdalFormat, RSGISLibDataType outDataType, std::vector<RSGISCmdsHistSummariseStats> exportStats) 
    {
        GDALAllRegister();
        try
        {
            if(exportStats.empty())
            {
                throw rsgis::RSGISHistoCubeException("No summary stats where provided");
            }
            
            std::vector<rsgis::math::rsgissummarytype> rsgisExportStats;
            for(std::vector<RSGISCmdsHistSummariseStats>::iterator iterStats = exportStats.begin(); iterStats != exportStats.end(); ++iterStats)
            {
                if((*iterStats) == rsgiscmds_hstat_min)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_min);
                }
                else if((*iterStats) == rsgiscmds_hstat_max)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_max);
                }
                else if((*iterStats) == rsgiscmds_hstat_mean)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_mean);
                }
                else if((*iterStats) == rsgiscmds_hstat_stddev)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_stddev);
                }
                else if((*iterStats) == rsgiscmds_hstat_median)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_median);
                }
                else if((*iterStats) == rsgiscmds_hstat_range)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_range);
                }
                else if((*iterStats) == rsgiscmds_hstat_mode)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_mode);
                }
                else if((*iterStats) == rsgiscmds_hstat_sum)
                {
                    rsgisExportStats.push_back(rsgis::math::sumtype_sum);
                }
                else
                {
                    throw rsgis::RSGISHistoCubeException("Summary static was not recognised.");
                }
            }
            
            rsgis::histocube::RSGISHistoCubeFile histoCubeFileObj = rsgis::histocube::RSGISHistoCubeFile();
            histoCubeFileObj.openFile(histCubeFile, true);
            
            std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*> *cubeLayers = histoCubeFileObj.getCubeLayersList();
            rsgis::histocube::RSGISHistCubeLayerMeta *cubeLayer = NULL;
            bool found = false;
            for(std::vector<rsgis::histocube::RSGISHistCubeLayerMeta*>::iterator iterLayers = cubeLayers->begin(); iterLayers != cubeLayers->end(); ++iterLayers)
            {
                if((*iterLayers)->name == layerName)
                {
                    cubeLayer = (*iterLayers);
                    found = true;
                    break;
                }
            }
            
            if(!found)
            {
                throw rsgis::RSGISHistoCubeException("Column was not found within the histogram cube.");
            }
            
            GDALDataset *dataset = (GDALDataset *) GDALOpen(clumpsImg.c_str(), GA_ReadOnly);
            if(dataset == NULL)
            {
                std::string message = std::string("Could not open image ") + clumpsImg;
                throw rsgis::RSGISImageException(message.c_str());
            }
            
            if(dataset->GetRasterCount() != 1)
            {
                GDALClose(dataset);
                throw rsgis::RSGISImageException("The clumps image must only have 1 image band.");
            }
            
            unsigned int maxRow = histoCubeFileObj.getNumFeatures()-1;
            unsigned int nBins = cubeLayer->bins.size();
            unsigned long dataArrLen = (maxRow*nBins)+nBins;
            unsigned int *dataArr = new unsigned int[dataArrLen];
            histoCubeFileObj.getHistoRows(layerName, 0, maxRow, dataArr, dataArrLen);
            
            std::cout << "Scale = " << cubeLayer->scale << std::endl;
            std::cout << "Offset = " << cubeLayer->offset << std::endl;
            
            rsgis::histocube::RSGISExportHistSummaryStats2ImgBands expHistSums2Img = rsgis::histocube::RSGISExportHistSummaryStats2ImgBands(rsgisExportStats.size(), dataArr, dataArrLen, nBins, cubeLayer->scale, cubeLayer->offset, rsgisExportStats);
            rsgis::img::RSGISCalcImage calcImg = rsgis::img::RSGISCalcImage(&expHistSums2Img);
            calcImg.calcImage(&dataset, 1, 0, outputImg, false, NULL, gdalFormat, RSGIS_to_GDAL_Type(outDataType));
            
            delete[] dataArr;
            GDALClose(dataset);
        }
        catch(rsgis::RSGISImageException &e)
        {
            throw RSGISCmdException(e.what());
        }
        catch(rsgis::RSGISHistoCubeException &e)
        {
            throw RSGISCmdException(e.what());
        }
    }

}}




