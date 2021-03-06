/*
 *  RSGISClumpImage.h
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 21/12/2011.
 *  Copyright 2011 RSGISLib.
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

#ifndef RSGISClumpImage_h
#define RSGISClumpImage_h


#include <iostream>
#include <string>

#include "gdal_priv.h"

#include "img/RSGISImageBandException.h"
#include "img/RSGISImageCalcException.h"
#include "img/RSGISImageUtils.h"
#include "img/RSGISCalcImgAlongsideOut.h"
#include "img/RSGISCalcImageValue.h"

// mark all exported classes/functions with DllExport to have
// them exported by Visual Studio
#undef DllExport
#ifdef _MSC_VER
    #ifdef rsgis_img_EXPORTS
        #define DllExport   __declspec( dllexport )
    #else
        #define DllExport   __declspec( dllimport )
    #endif
#else
    #define DllExport
#endif

namespace rsgis 
{
	namespace img
	{
        class DllExport RSGISClumpImage : public RSGISCalcImgValueAlongsideOut
        {
        public:
            RSGISClumpImage():RSGISCalcImgValueAlongsideOut()
            {
                this->clumpCounter = 1;
            };
            bool calcValue(bool firstIter, unsigned int numBands, unsigned int *dataCol, unsigned int **rowAbove, unsigned int **rowBelow, unsigned int *left, unsigned int *right);
            ~RSGISClumpImage(){};
        private:
            long clumpCounter;
        };
        
        
        class DllExport RSGISUniquePixelClumps : public RSGISCalcImageValue
        {
        public:
            RSGISUniquePixelClumps(bool noDataDefined, float noDataVal);
            void calcImageValue(float *bandValues, int numBands, double *output);
            void calcImageValue(float *bandValues, int numBands) {throw RSGISImageCalcException("No implemented");};
            void calcImageValue(long *intBandValues, unsigned int numIntVals, float *floatBandValues, unsigned int numfloatVals) {throw RSGISImageCalcException("Not implemented");};
            void calcImageValue(long *intBandValues, unsigned int numIntVals, float *floatBandValues, unsigned int numfloatVals, double *output) {throw RSGISImageCalcException("Not implemented");};
            void calcImageValue(long *intBandValues, unsigned int numIntVals, float *floatBandValues, unsigned int numfloatVals, geos::geom::Envelope extent){throw rsgis::img::RSGISImageCalcException("Not implemented");};
            void calcImageValue(float *bandValues, int numBands, geos::geom::Envelope extent) {throw RSGISImageCalcException("No implemented");};
            void calcImageValue(float *bandValues, int numBands, double *output, geos::geom::Envelope extent) {throw RSGISImageCalcException("No implemented");};
            void calcImageValue(float ***dataBlock, int numBands, int winSize, double *output) {throw RSGISImageCalcException("No implemented");};
            void calcImageValue(float ***dataBlock, int numBands, int winSize, double *output, geos::geom::Envelope extent) {throw RSGISImageCalcException("No implemented");};
            bool calcImageValueCondition(float ***dataBlock, int numBands, int winSize, double *output) {throw RSGISImageCalcException("No implemented");};
            ~RSGISUniquePixelClumps();
        private:
            bool noDataDefined;
            float noDataVal;
            size_t nextPixelVal;
        };
	}
}

#endif
