/*
 *  RSGISCmdImageCalibration.cpp
 *
 *
 *  Created by Pete Bunting on 10/07/2013.
 *  Copyright 2013 RSGISLib.
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

#include "RSGISCmdImageCalibration.h"
#include "RSGISCmdParent.h"

#include "calibration/RSGISStandardDN2RadianceCalibration.h"
#include "calibration/RSGISCalculateTopOfAtmosphereReflectance.h"

#include "img/RSGISImageCalcException.h"
#include "img/RSGISCalcImageValue.h"
#include "img/RSGISCalcImage.h"

namespace rsgis{ namespace cmds {
    
    void executeConvertLandsat2Radiance(std::string outputImage, std::string gdalFormat, std::vector<CmdsLandsatRadianceGainsOffsets> landsatRadGainOffs)throw(RSGISCmdException)
    {
        GDALAllRegister();
        
        try
        {
            unsigned int numBands = landsatRadGainOffs.size();
            GDALDataset **datasets = new GDALDataset*[numBands];
            std::string *outBandNames = new std::string[numBands];
            
            rsgis::calib::LandsatRadianceGainsOffsets *lsRadGainOffs = new rsgis::calib::LandsatRadianceGainsOffsets[numBands];
            
            unsigned int i = 0;
            unsigned int numRasterBands = 0;
            unsigned int totalNumRasterBands = 0;
            for(std::vector<rsgis::cmds::CmdsLandsatRadianceGainsOffsets>::iterator iterBands = landsatRadGainOffs.begin(); iterBands != landsatRadGainOffs.end(); ++iterBands)
			{
                std::cout << "Opening: " << (*iterBands).imagePath << std::endl;
                
                datasets[i] = (GDALDataset *) GDALOpen((*iterBands).imagePath.c_str(), GA_ReadOnly);
                if(datasets[i] == NULL)
                {
                    std::string message = std::string("Could not open image ") + (*iterBands).imagePath;
                    throw RSGISImageException(message.c_str());
                }
                
                numRasterBands = datasets[i]->GetRasterCount();
                
                if((*iterBands).band > numRasterBands)
                {
                    throw RSGISImageException("You have specified a band which is not within the image");
                }
                lsRadGainOffs[i].band = totalNumRasterBands + (*iterBands).band-1;
                
                lsRadGainOffs[i].lMax = (*iterBands).lMax;
                lsRadGainOffs[i].lMin = (*iterBands).lMin;
                lsRadGainOffs[i].qCalMax = (*iterBands).qCalMax;
                lsRadGainOffs[i].qCalMin = (*iterBands).qCalMin;
                
                outBandNames[i] = (*iterBands).bandName;
                
                totalNumRasterBands += numRasterBands;
                ++i;
			}
            
            rsgis::calib::RSGISLandsatRadianceCalibration *radianceCalibration = new rsgis::calib::RSGISLandsatRadianceCalibration(numBands, lsRadGainOffs);
            rsgis::img::RSGISCalcImage *calcImage = new rsgis::img::RSGISCalcImage(radianceCalibration, "", true);
 
            calcImage->calcImage(datasets, numBands, outputImage, true, outBandNames, gdalFormat);
            
            for(unsigned int i = 0; i < numBands; ++i)
            {
                GDALClose(datasets[i]);
            }
            
            delete[] datasets;
            delete[] lsRadGainOffs;
            delete[] outBandNames;
            
            delete radianceCalibration;
            delete calcImage;
        }
        catch(RSGISException &e)
        {
            throw RSGISCmdException(e.what());
        }
        catch(std::exception &e)
        {
            throw RSGISCmdException(e.what());
        }
    }
    
    
    
    void executeConvertRadiance2TOARefl(std::string inputImage, std::string outputImage, std::string gdalFormat, rsgis::RSGISLibDataType rsgisOutDataType, float scaleFactor, unsigned int julianDay, bool useJulianDay, unsigned int year, unsigned int month, unsigned int day, float solarZenith, float *solarIrradiance, unsigned int numBands) throw(RSGISCmdException)
    {
        GDALAllRegister();
        GDALDataset **datasets = NULL;
        rsgis::calib::RSGISCalculateTopOfAtmosphereReflectance *calcTopAtmosRefl = NULL;
        rsgis::img::RSGISCalcImage *calcImage = NULL;
        
        try
        {
            datasets = new GDALDataset*[1];
            
            std::cout << "Open " << inputImage << std::endl;
            datasets[0] = (GDALDataset *) GDALOpen(inputImage.c_str(), GA_ReadOnly);
            if(datasets[0] == NULL)
            {
                std::string message = std::string("Could not open image ") + inputImage;
                throw rsgis::RSGISImageException(message.c_str());
            }
            
            unsigned int numRasterBands = datasets[0]->GetRasterCount();
            if(numBands != numRasterBands)
            {
                GDALClose(datasets[0]);
                delete[] datasets;
                throw rsgis::RSGISException("The number of input image bands and solar irradiance values are different.");
            }
            
            double solarDistance = 0;
            
            solarDistance = rsgis::calib::rsgisCalcSolarDistance(julianDay);

            
            calcTopAtmosRefl = new rsgis::calib::RSGISCalculateTopOfAtmosphereReflectance(numRasterBands, solarIrradiance, solarDistance, solarZenith, scaleFactor);
            
            calcImage = new rsgis::img::RSGISCalcImage(calcTopAtmosRefl, "", true);
            calcImage->calcImage(datasets, 1, outputImage, false, NULL, gdalFormat, RSGIS_to_GDAL_Type(rsgisOutDataType));
            
            GDALClose(datasets[0]);
            delete[] datasets;
            
            delete calcTopAtmosRefl;
            delete calcImage;
        }
        catch(RSGISException &e)
        {
            throw RSGISCmdException(e.what());
        }
        catch(std::exception &e)
        {
            throw RSGISCmdException(e.what());
        }
    }
    
}}


