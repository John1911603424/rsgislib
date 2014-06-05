/*
 *  RSGISSelectClumps.cpp
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 13/09/2013.
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

#include "RSGISSelectClumps.h"


namespace rsgis{namespace rastergis{
    
    RSGISSelectClumpsOnGrid::RSGISSelectClumpsOnGrid()
    {
        
    }
    
    void RSGISSelectClumpsOnGrid::selectClumpsOnGrid(GDALDataset *clumpsDataset, std::string inSelectField, std::string outSelectField, std::string eastingsField, std::string northingsField, std::string metricField, unsigned int rows, unsigned int cols, RSGISSelectMethods method)throw(rsgis::RSGISAttributeTableException)
    {
        try
        {
            std::cout << "Import attribute tables to memory.\n";
            GDALRasterAttributeTable *gdalRAT = clumpsDataset->GetRasterBand(1)->GetDefaultRAT();
            
            RSGISRasterAttUtils attUtils;
            rsgis::img::RSGISImageUtils imgUtils;
            
            unsigned int inSelectIdx = attUtils.findColumnIndex(gdalRAT, inSelectField);
            unsigned int eastingsIdx = attUtils.findColumnIndex(gdalRAT, eastingsField);
            unsigned int northingsIdx = attUtils.findColumnIndex(gdalRAT, northingsField);
            unsigned int metricIdx = attUtils.findColumnIndex(gdalRAT, metricField);
            unsigned int outSelectIdx = attUtils.findColumnIndexOrCreate(gdalRAT, outSelectField, GFT_Integer);
            
            unsigned int numTiles = rows * cols;
            std::cout << "Number of Tiles: " << numTiles << std::endl;
            
            OGREnvelope *imgExtent = imgUtils.getSpatialExtent(clumpsDataset);
            double imgWidth = imgExtent->MaxX - imgExtent->MinX;
            double imgHeight = imgExtent->MaxY - imgExtent->MinY;
            
            //std::cout << "Image Width = " << imgWidth << std::endl;
            //std::cout << "Image Height = " << imgHeight << std::endl;
            
            double tileWidth = imgWidth / ((double)cols);
            double tileHeight = imgHeight / ((double)rows);
            
            std::cout << "Tile Width = " << tileWidth << std::endl;
            std::cout << "Tile Height = " << tileHeight << std::endl;
            
            double *selectVal = new double[numTiles];
            unsigned int *selectIdx = new unsigned int[numTiles];
            std::vector<unsigned int> **tileIdxs = new std::vector<unsigned int>*[numTiles];
            OGREnvelope **tilesEnvs = new OGREnvelope*[numTiles];
            unsigned int idx = 0;
            double tileMinX = 0;
            double tileMaxX = 0;
            double tileMaxY = imgExtent->MaxY;
            double tileMinY = tileMaxY - tileHeight;
            bool *first = new bool[numTiles];
            for(unsigned int i = 0; i < numTiles; ++i)
            {
                first[i] = true;
            }
            for(unsigned int r = 0; r < rows; ++r)
            {
                tileMinX = imgExtent->MinX;
                tileMaxX = tileMinX + tileWidth;
                for(unsigned int c = 0; c < cols; ++c)
                {
                    idx = c + (r * cols);
                    tileIdxs[idx] = new std::vector<unsigned int>();
                    tilesEnvs[idx] = new OGREnvelope();
                    first[idx] = true;
                    
                    tilesEnvs[idx]->MinX = tileMinX;
                    tilesEnvs[idx]->MaxX = tileMaxX;
                    tilesEnvs[idx]->MinY = tileMinY;
                    tilesEnvs[idx]->MaxY = tileMaxY;
                    
                    tileMinX = tileMinX + tileWidth;
                    tileMaxX = tileMaxX + tileWidth;
                    selectVal[idx] = 0;
                    selectIdx[idx] = 0;
                }
                tileMaxY = tileMaxY - tileHeight;
                tileMinY = tileMinY - tileHeight;
            }
            
            RSGISCalcTileStats calcTileStats = RSGISCalcTileStats(rows, cols, selectVal, selectIdx, tileIdxs, tilesEnvs, first, method);
            RSGISRATCalc ratCalc = RSGISRATCalc(&calcTileStats);
            std::vector<unsigned int> inRealColIdx;
            inRealColIdx.push_back(eastingsIdx);
            inRealColIdx.push_back(northingsIdx);
            inRealColIdx.push_back(metricIdx);
            std::vector<unsigned int> inIntColIdx;
            inIntColIdx.push_back(inSelectIdx);
            std::vector<unsigned int> inStrColIdx;
            std::vector<unsigned int> outRealColIdx;
            std::vector<unsigned int> outIntColIdx;
            std::vector<unsigned int> outStrColIdx;
            ratCalc.calcRATValues(gdalRAT, inRealColIdx, inIntColIdx, inStrColIdx, outRealColIdx, outIntColIdx, outStrColIdx);
            
            if(method == meanMethod)
            {
                idx = 0;
                for(unsigned int r = 0; r < rows; ++r)
                {
                    for(unsigned int c = 0; c < cols; ++c)
                    {
                        idx = c + (r * cols);
                        if(tileIdxs[idx]->size() > 0)
                        {
                            selectVal[idx] = selectVal[idx] / tileIdxs[idx]->size();
                        }
                        else
                        {
                            selectIdx[idx] = 0;
                        }
                    }
                }
                
                for(unsigned int i = 0; i < numTiles; ++i)
                {
                    first[i] = true;
                }
                
                double *selectDistVal = new double[numTiles];
                RSGISSelectClumpClosest2TileMean calcSelectMeanIdx = RSGISSelectClumpClosest2TileMean(rows, cols, selectVal, selectDistVal, selectIdx, tileIdxs, tilesEnvs, first);
                ratCalc = RSGISRATCalc(&calcSelectMeanIdx);
                inRealColIdx.clear();
                inRealColIdx.push_back(eastingsIdx);
                inRealColIdx.push_back(northingsIdx);
                inRealColIdx.push_back(metricIdx);
                inIntColIdx.clear();
                inIntColIdx.push_back(inSelectIdx);
                inStrColIdx.clear();
                outRealColIdx.clear();
                outIntColIdx.clear();
                outStrColIdx.clear();
                ratCalc.calcRATValues(gdalRAT, inRealColIdx, inIntColIdx, inStrColIdx, outRealColIdx, outIntColIdx, outStrColIdx);
                delete selectDistVal;
            }
            /*
            for(unsigned int i = 0; i < numTiles; ++i)
            {
                std::cout << "Tile Size: " << tileIdxs[i]->size() << std::endl;
                std::cout << "\tTile " << i << " = " << selectVal[i] << " index " << selectIdx[i] << std::endl;
            }
            */
            
            std::cout << "Writing to the output column\n";
            RSGISWriteSelectedClumpsColumn outSelectedClumps = RSGISWriteSelectedClumpsColumn(selectIdx, numTiles);
            ratCalc = RSGISRATCalc(&outSelectedClumps);
            inRealColIdx.clear();
            inIntColIdx.clear();
            inStrColIdx.clear();
            outRealColIdx.clear();
            outIntColIdx.clear();
            outIntColIdx.push_back(outSelectIdx);
            outStrColIdx.clear();
            ratCalc.calcRATValues(gdalRAT, inRealColIdx, inIntColIdx, inStrColIdx, outRealColIdx, outIntColIdx, outStrColIdx);
            
            
            // Clean up memory.
            idx = 0;
            for(unsigned int r = 0; r < rows; ++r)
            {
                for(unsigned int c = 0; c < cols; ++c)
                {
                    idx = c + (r * cols);
                    
                    delete tileIdxs[idx];
                    delete tilesEnvs[idx];
                }
            }
            
            delete[] first;
            delete[] tileIdxs;
            delete[] tilesEnvs;
            delete[] selectVal;
            delete[] selectIdx;
            
        }
        catch (RSGISAttributeTableException &e)
        {
            throw e;
        }
        catch (RSGISException &e)
        {
            throw RSGISAttributeTableException(e.what());
        }
    }
    
    RSGISSelectClumpsOnGrid::~RSGISSelectClumpsOnGrid()
    {
        
    }
    
    
    RSGISCalcTileStats::RSGISCalcTileStats(unsigned int numRows, unsigned int numCols, double *selectVal, unsigned int *selectIdx, std::vector<unsigned int> **tileIdxs, OGREnvelope **tilesEnvs, bool *first, RSGISSelectMethods method):RSGISRATCalcValue()
    {
        this->numRows = numRows;
        this->numCols = numCols;
        this->selectVal = selectVal;
        this->selectIdx = selectIdx;
        this->tileIdxs = tileIdxs;
        this->tilesEnvs = tilesEnvs;
        this->first = first;
        this->method = method;
    }
    
    void RSGISCalcTileStats::calcRATValue(size_t fid, double *inRealCols, unsigned int numInRealCols, int *inIntCols, unsigned int numInIntCols, std::string *inStringCols, unsigned int numInStringCols, double *outRealCols, unsigned int numOutRealCols, int *outIntCols, unsigned int numOutIntCols, std::string *outStringCols, unsigned int numOutStringCols) throw(RSGISAttributeTableException)
    {
        if(inIntCols[0] == 1)
        {
            bool foundTile = false;
            unsigned int idx = 0;
            unsigned int foundTileIdx = 0;
            double eastings = inRealCols[0];
            double northings = inRealCols[1];
            for(unsigned int r = 0; r < numRows; ++r)
            {
                for(unsigned int c = 0; c < numCols; ++c)
                {
                    idx = c + (r * numCols);
                    if( ((eastings >= tilesEnvs[idx]->MinX) & (eastings <= tilesEnvs[idx]->MaxX)) &
                       ((northings >= tilesEnvs[idx]->MinY) & (northings <= tilesEnvs[idx]->MaxY)))
                    {
                        tileIdxs[idx]->push_back(fid);
                        foundTileIdx = idx;
                        foundTile = true;
                        break;
                    }
                }
                if(foundTile)
                {
                    break;
                }
            }
            
            if(foundTile)
            {
                double metricVal = inRealCols[2];
                if(first[foundTileIdx])
                {
                    first[foundTileIdx] = false;
                    selectVal[foundTileIdx] = metricVal;
                    selectIdx[foundTileIdx] = fid;
                }
                else
                {
                    if(method == meanMethod)
                    {
                        selectVal[foundTileIdx] += metricVal;
                    }
                    else if((method == minMethod) & (metricVal < selectVal[foundTileIdx]))
                    {
                        selectVal[foundTileIdx] = metricVal;
                        selectIdx[foundTileIdx] = fid;
                    }
                    else if((method == minMethod) & (metricVal > selectVal[foundTileIdx]))
                    {
                        selectVal[foundTileIdx] = metricVal;
                        selectIdx[foundTileIdx] = fid;
                    }
                }
            }
        }
    }
    
    RSGISCalcTileStats::~RSGISCalcTileStats()
    {
        
    }
    
    
    
    
    RSGISSelectClumpClosest2TileMean::RSGISSelectClumpClosest2TileMean(unsigned int numRows, unsigned int numCols, double *selectVal, double *selectDistVal, unsigned int *selectIdx, std::vector<unsigned int> **tileIdxs, OGREnvelope **tilesEnvs, bool *first):RSGISRATCalcValue()
    {
        this->numRows = numRows;
        this->numCols = numCols;
        this->selectVal = selectVal;
        this->selectIdx = selectIdx;
        this->tileIdxs = tileIdxs;
        this->tilesEnvs = tilesEnvs;
        this->first = first;
    }
    
    void RSGISSelectClumpClosest2TileMean::calcRATValue(size_t fid, double *inRealCols, unsigned int numInRealCols, int *inIntCols, unsigned int numInIntCols, std::string *inStringCols, unsigned int numInStringCols, double *outRealCols, unsigned int numOutRealCols, int *outIntCols, unsigned int numOutIntCols, std::string *outStringCols, unsigned int numOutStringCols) throw(RSGISAttributeTableException)
    {
        if(inIntCols[0] == 1)
        {
            bool foundTile = false;
            unsigned int idx = 0;
            unsigned int foundTileIdx = 0;
            double eastings = inRealCols[0];
            double northings = inRealCols[1];
            for(unsigned int r = 0; r < numRows; ++r)
            {
                for(unsigned int c = 0; c < numCols; ++c)
                {
                    idx = c + (r * numCols);
                    if( ((eastings >= tilesEnvs[idx]->MinX) & (eastings <= tilesEnvs[idx]->MaxX)) &
                       ((northings >= tilesEnvs[idx]->MinY) & (northings <= tilesEnvs[idx]->MaxY)))
                    {
                        tileIdxs[idx]->push_back(fid);
                        foundTileIdx = idx;
                        foundTile = true;
                        break;
                    }
                }
                if(foundTile)
                {
                    break;
                }
            }
            
            if(foundTile)
            {
                double metricValDist = pow((inRealCols[2] - selectVal[foundTileIdx]), 2.0);
                if(first[foundTileIdx])
                {
                    selectDistVal[foundTileIdx] = metricValDist;
                    selectIdx[foundTileIdx] = fid;
                }
                else if(metricValDist < selectDistVal[foundTileIdx])
                {
                    selectDistVal[foundTileIdx] = metricValDist;
                    selectIdx[foundTileIdx] = fid;
                }
            }
        }
    }
    
    RSGISSelectClumpClosest2TileMean::~RSGISSelectClumpClosest2TileMean()
    {
        
    }
    
    
    RSGISWriteSelectedClumpsColumn::RSGISWriteSelectedClumpsColumn(unsigned int *selectIdx, unsigned int numIdxes):RSGISRATCalcValue()
    {
        this->selectIdx = selectIdx;
        this->numIdxes = numIdxes;
    }
    
    void RSGISWriteSelectedClumpsColumn::calcRATValue(size_t fid, double *inRealCols, unsigned int numInRealCols, int *inIntCols, unsigned int numInIntCols, std::string *inStringCols, unsigned int numInStringCols, double *outRealCols, unsigned int numOutRealCols, int *outIntCols, unsigned int numOutIntCols, std::string *outStringCols, unsigned int numOutStringCols) throw(RSGISAttributeTableException)
    {
        if(fid > 0)
        {
            bool found = false;
            for(unsigned int i = 0; i < numIdxes; ++i)
            {
                if(fid == selectIdx[i])
                {
                    found = true;
                    break;
                }
            }
            
            if(found)
            {
                outIntCols[0] = 1;
            }
            else
            {
                outIntCols[0] = 0;
            }
        }
    }
    
    RSGISWriteSelectedClumpsColumn::~RSGISWriteSelectedClumpsColumn()
    {
        
    }
    
    
    
}}


