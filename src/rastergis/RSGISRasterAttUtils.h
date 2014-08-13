/*
 *  RSGISRasterAttUtils.h
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 01/08/2012.
 *  Copyright 2012 RSGISLib.
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

#ifndef RSGISRasterAttUtils_H
#define RSGISRasterAttUtils_H

#define RAT_BLOCK_LENGTH 100000 // Define block length (Default block length for KEA is 1000)

#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <vector>
#include <math.h>

#include "gdal_priv.h"
#include "gdal_rat.h"

#include "libkea/KEAImageIO.h"

#include "common/RSGISAttributeTableException.h"

#include "utils/RSGISColour.h"

#include <boost/numeric/conversion/cast.hpp>
#include <boost/lexical_cast.hpp>

namespace rsgis{namespace rastergis{
    
    inline int RSGISRATStatsTextProgress( double dfComplete, const char *pszMessage, void *pData)
    {
        int nPercent = int(dfComplete*100);
        int *pnLastComplete = (int*)pData;
        
        if(nPercent < 10)
        {
            nPercent = 0;
        }
        else if(nPercent < 20)
        {
            nPercent = 10;
        }
        else if(nPercent < 30)
        {
            nPercent = 20;
        }
        else if(nPercent < 40)
        {
            nPercent = 30;
        }
        else if(nPercent < 50)
        {
            nPercent = 40;
        }
        else if(nPercent < 60)
        {
            nPercent = 50;
        }
        else if(nPercent < 70)
        {
            nPercent = 60;
        }
        else if(nPercent < 80)
        {
            nPercent = 70;
        }
        else if(nPercent < 90)
        {
            nPercent = 80;
        }
        else if(nPercent < 95)
        {
            nPercent = 90;
        }
        else
        {
            nPercent = 100;
        }
        
        if( (pnLastComplete != NULL) && (nPercent != *pnLastComplete ))
        {
            if(nPercent == 0)
            {
                std::cout << "Started ." << nPercent << "." << std::flush;
            }
            else if(nPercent == 100)
            {
                std::cout << "." << nPercent << ". Complete." << std::endl;
            }
            else
            {
                std::cout << "." << nPercent << "." << std::flush;
            }
        }
        
        *pnLastComplete = nPercent;
        
        return true;
    };
    
    class RSGISRasterAttUtils
    {
    public:
        RSGISRasterAttUtils();
        void copyAttColumns(GDALDataset *inImage, GDALDataset *outImage, std::vector<std::string> fields,  bool copyColours=true, bool copyHist=true, int ratBand=1) throw(RSGISAttributeTableException);
        void copyColourForCats(GDALDataset *catsImage, GDALDataset *classImage, std::string classField) throw(RSGISAttributeTableException);
        void exportColumns2ASCII(GDALDataset *inImage, std::string outputFile, std::vector<std::string> fields, int ratBand=1) throw(RSGISAttributeTableException);
        void translateClasses(GDALDataset *inImage, std::string classInField, std::string classOutField, std::map<size_t, size_t> classPairs) throw(RSGISAttributeTableException);
        void applyClassColours(GDALDataset *inImage, std::string classInField, std::map<size_t, rsgis::utils::RSGISColourInt> classColoursPairs, int ratBand=1) throw(RSGISAttributeTableException);
        void applyClassStrColours(GDALDataset *inImage, std::string classInField, std::map<std::string, rsgis::utils::RSGISColourInt> classColoursPairs, int ratBand=1) throw(RSGISAttributeTableException);
        unsigned int findColumnIndex(const GDALRasterAttributeTable *gdalATT, std::string colName) throw(RSGISAttributeTableException);
        unsigned int findColumnIndexOrCreate(GDALRasterAttributeTable *gdalATT, std::string colName, GDALRATFieldType dType, GDALRATFieldUsage dUsage=GFU_Generic) throw(RSGISAttributeTableException);
        double readDoubleColumnVal(const GDALRasterAttributeTable *gdalATT, std::string colName, unsigned int row) throw(RSGISAttributeTableException);
        long readIntColumnVal(const GDALRasterAttributeTable *gdalATT, std::string colName, unsigned int row) throw(RSGISAttributeTableException);
        std::string readStringColumnVal(const GDALRasterAttributeTable *gdalATT, std::string colName, unsigned int row) throw(RSGISAttributeTableException);
        
        double* readDoubleColumn(GDALRasterAttributeTable *attTable, std::string colName, size_t *colLen) throw(RSGISAttributeTableException);
        int* readIntColumn(GDALRasterAttributeTable *attTable, std::string colName, size_t *colLen) throw(RSGISAttributeTableException);
        char** readStrColumn(GDALRasterAttributeTable *attTable, std::string colName, size_t *colLen) throw(RSGISAttributeTableException);
        
        std::vector<std::vector<size_t>* >* getRATNeighbours(GDALDataset *clumpImage, unsigned int ratBand) throw(RSGISAttributeTableException);
        
        ~RSGISRasterAttUtils();
    };
	
}}

#endif

