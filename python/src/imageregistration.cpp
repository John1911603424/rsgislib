/*
 *  imageregistration.cpp
 *  RSGIS_LIB
 *
 *  Created by Dan Clewley on 08/09/2013.
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

#include "rsgispy_common.h"
#include "cmds/RSGISCmdImageRegistration.h"

/* An exception object for this module */
/* created in the init function */
struct ImageRegistrationState
{
    PyObject *error;
};

#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct ImageRegistrationState*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct ImageRegistrationState _state;
#endif

static PyObject *ImageRegistration_BasicRegistration(PyObject *self, PyObject *args)
{
    const char *pszInputReferenceImage, *pszInputFloatingmage, *pszOutputGCPFile;
    int pixelGap, windowSize, searchArea, subPixelResolution, metricType, outputType;
    float threshold, stdDevRefThreshold, stdDevFloatThreshold;
    
    if( !PyArg_ParseTuple(args, "ssifiiffiiis:basicregistration", &pszInputReferenceImage, &pszInputFloatingmage, &pixelGap, 
                                &threshold, &windowSize, &searchArea, &stdDevRefThreshold, &stdDevFloatThreshold, &subPixelResolution, 
                                &metricType, &outputType, &pszOutputGCPFile))
        return NULL;

    try
    {
        rsgis::cmds:: excecuteBasicRegistration(pszInputReferenceImage, pszInputFloatingmage, pixelGap,
                                    threshold, windowSize, searchArea, stdDevRefThreshold,
                                    stdDevFloatThreshold, subPixelResolution, metricType,
                                    outputType, pszOutputGCPFile);
    }
    catch(rsgis::cmds::RSGISCmdException &e)
    {
        PyErr_SetString(GETSTATE(self)->error, e.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *ImageRegistration_SingleLayerRegistration(PyObject *self, PyObject *args)
{
    const char *pszInputReferenceImage, *pszInputFloatingmage, *pszOutputGCPFile;
    int pixelGap, windowSize, searchArea, subPixelResolution, metricType, 
        outputType, maxNumIterations, distanceThreshold;
    float threshold, stdDevRefThreshold, stdDevFloatThreshold, moveChangeThreshold,
        pSmoothness;
    
    if( !PyArg_ParseTuple(args, "ssifiiffiiiffiis:singlelayerregistration", &pszInputReferenceImage, &pszInputFloatingmage, &pixelGap, 
                                &threshold, &windowSize, &searchArea, &stdDevRefThreshold, &stdDevFloatThreshold, &subPixelResolution,
                                &distanceThreshold, &maxNumIterations, &moveChangeThreshold, &pSmoothness,
                                &metricType, &outputType, &pszOutputGCPFile))
        return NULL;

    try
    {
        rsgis::cmds:: excecuteSingleLayerConnectedRegistration(pszInputReferenceImage, pszInputFloatingmage, pixelGap,
                                    threshold, windowSize, searchArea, stdDevRefThreshold,
                                    stdDevFloatThreshold, subPixelResolution, distanceThreshold,
                                    maxNumIterations, moveChangeThreshold, pSmoothness, metricType,
                                    outputType, pszOutputGCPFile);
    }
    catch(rsgis::cmds::RSGISCmdException &e)
    {
        PyErr_SetString(GETSTATE(self)->error, e.what());
        return NULL;
    }

    Py_RETURN_NONE;
}



// Our list of functions in this module
static PyMethodDef ImageRegistrationMethods[] = {
    {"basicregistration", ImageRegistration_BasicRegistration, METH_VARARGS, 
"imageregistration.basicregistration(reference, floating, pixelGap, threshold, window, search, stddevRef, stddevFloat, subpixelresolution, metric, outputType, output)\n"
"Extract pixel value for each point in a shape file and output as a shapefile.\n"
"where:\n"
" * reference is a string providing reference image which to which the floating image is to be registered.n"
" * floating is a string providing the floating image to be registered to the reference image\n"
" * pixelGap is an int specifying the gap, in image pixels, between the initial tie points (this is for both the x and y axis) \n"
" * threshold is a float providing the threshold for the image metric above/below (depending on image metric)\n"
"        which matching is consider insufficient to be reliable and therefore the match will be ignored.\n"
" * window is an int providing the size of the window around each tie point which will be used for the matching \n"
" * search is an int providing the distance (in pixels) from the tie point start point which will be searched.\n"
" * stddevRef is a float which defines the standard deviation for the window around each tie point below which it is \n"
"        deemed there is insufficient information to perform a match \n"
" * stddevFloat is a float which defines the standard deviation for the window around each tie point below which it is \n"
"        deemed there is insufficient information to perform a match \n"
"Note, that the tie point window has to be below the threshold for both the reference and floating image to be ignored\n"
" * subpixelresolution is an int specifying the sub-pixel resolution to which the pixel shifts are estimated.\n"
"      Note that the values are positive integers such that a value of 2 will result in a sub pixel resolution \n"
"      of 0.5 of a pixel and a value 4 will be 0.25 of a pixel. \n"
" * metric is an the similarity metric used to compare images of type rsgislib.imageregistration.METRIC_* \n"
" * outputType is an the format of the output file of type rsgislib.imageregistration.TYPE_* \n"
" * output is a string giving specifying the output file, containing the generated tie points\n"
"\n"
"Example::\n"
"\n"
"   reference = 'ref.kea'\n"        
"   floating = 'float.kea'\n"
"   pixelGap = 50\n"
"   threshold = 0.4\n"
"   window = 100\n"
"   search = 5\n"
"   stddevRef = 2\n"
"   stddevFloat = 2\n"
"   subpixelresolution = 4\n"
"   metric = imageregistration.METRIC_CORELATION\n"
"   outputType = imageregistration.TYPE_RSGIS_IMG2MAP\n"
"   output = './TestOutputs/injune_p142_casi_sub_utm_tie_points.txt'\n"
"   imageregistration.basicregistration(reference, floating, pixelGap, threshold, window, search, stddevRef, stddevFloat, subpixelresolution, metric, outputType, output)\n"
"\n"
},

    {"singlelayerregistration", ImageRegistration_SingleLayerRegistration, METH_VARARGS, 
"imageregistration.singlelayerregistration(reference, floating, pixelGap, threshold, window, search, stddevRef, stddevFloat, subpixelresolution, distanceThreshold, maxiterations, movementThreshold, pSmoothness, metric, outputType, output)\n"
"where:\n"
"Extract pixel value for each point in a shape file and output as a shapefile.\n"
" * reference is a string providing reference image which to which the floating image is to be registered.n"
" * floating is a string providing the floating image to be registered to the reference image\n"
" * pixelGap is an int specifying the gap, in image pixels, between the initial tie points (this is for both the x and y axis) \n"
" * threshold is a float providing the threshold for the image metric above/below (depending on image metric)\n"
"        which matching is consider insufficient to be reliable and therefore the match will be ignored.\n"
" * window is an int providing the size of the window around each tie point which will be used for the matching \n"
" * search is an int providing the distance (in pixels) from the tie point start point which will be searched.\n"
" * stddevRef is a float which defines the standard deviation for the window around each tie point below which it is \n"
"        deemed there is insufficient information to perform a match \n"
" * stddevFloat is a float which defines the standard deviation for the window around each tie point below which it is \n"
"        deemed there is insufficient information to perform a match \n"
"Note, that the tie point window has to be below the threshold for both the reference and floating image to be ignored\n"
" * subpixelresolution is an int specifying the sub-pixel resolution to which the pixel shifts are estimated.\n"
"      Note that the values are positive integers such that a value of 2 will result in a sub pixel resolution \n"
"      of 0.5 of a pixel and a value 4 will be 0.25 of a pixel. \n"
" * distanceThreshold is an int giving the distance (in pixels) to be connected within the layer.\n"
" * maxiterations is an int giving the maximum number of iterations of the tie point grid to find an optimal set of tie points\n"
" * movementThreshold is a float providing the threshold for the average amount of tie point movement for the optimisation to be terminated\n"
" * pSmoothness is a float providing the 'p' parameter for the inverse weighted distance calculation. A value of 2 should be used by default\n"
" * metric is an the similarity metric used to compare images of type rsgislib.imageregistration.METRIC_* \n"
" * outputType is an the format of the output file of type rsgislib.imageregistration.TYPE_* \n"
" * output is a string giving specifying the output file, containing the generated tie points\n"
"\n"
"Example::\n"
"\n"
"   reference = 'ref.kea'\n"        
"   floating = 'float.kea'\n"
"   pixelGap = 50\n"
"   threshold = 0.4\n"
"   window = 100\n"
"   search = 5\n"
"   stddevRef = 2\n"
"   stddevFloat = 2\n"
"   subpixelresolution = 4\n"
"   metric = imageregistration.METRIC_CORELATION\n"
"   outputType = imageregistration.TYPE_RSGIS_IMG2MAP\n"
"   output = './TestOutputs/injune_p142_casi_sub_utm_tie_points.txt'\n"
"   imageregistration.basicregistration(reference, floating, pixelGap, threshold, window, search, stddevRef, stddevFloat, subpixelresolution, metric, outputType, output)\n"
"\n"
},
    {NULL}        /* Sentinel */
};


#if PY_MAJOR_VERSION >= 3

static int ImageRegistration_traverse(PyObject *m, visitproc visit, void *arg) 
{
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int ImageRegistration_clear(PyObject *m) 
{
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "_imageregistration",
        NULL,
        sizeof(struct ImageRegistrationState),
        ImageRegistrationMethods,
        NULL,
        ImageRegistration_traverse,
        ImageRegistration_clear,
        NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC 
PyInit__imageregistration(void)

#else
#define INITERROR return

PyMODINIT_FUNC
init_imageregistration(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *pModule = PyModule_Create(&moduledef);
#else
    PyObject *pModule = Py_InitModule("_imageregistration", ImageRegistrationMethods);
#endif
    if( pModule == NULL )
        INITERROR;

    struct ImageRegistrationState *state = GETSTATE(pModule);

    // Create and add our exception type
    state->error = PyErr_NewException("_imageregistration.error", NULL, NULL);
    if( state->error == NULL )
    {
        Py_DECREF(pModule);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return pModule;
#endif
}