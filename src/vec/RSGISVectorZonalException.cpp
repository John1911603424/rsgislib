/*
 *  RSGISVectorZonalException.cpp
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 02/05/2008.
 *  Copyright 2008 RSGISLib. All rights reserved.
 *  This file is part of RSGISLib.
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

#include "RSGISVectorZonalException.h"


namespace rsgis {namespace vec{
	
	RSGISVectorZonalException::RSGISVectorZonalException() : rsgis::RSGISVectorException("A RSGISVectorZonalException has been created..")
	{

	}
	
	
	RSGISVectorZonalException::RSGISVectorZonalException(const char* message) : rsgis::RSGISVectorException(message)
	{
		
	}
	
	RSGISVectorZonalException::RSGISVectorZonalException(std::string message) : rsgis::RSGISVectorException(message)
	{
		
	}
	
	
}} //rsgis::vec


