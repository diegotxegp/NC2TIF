#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Run: python3 <name> <dir> <epsg>
# Example: python3 .\nctocuttif.py P:\99_IMPACTOS COSTA\99_TEMPORAL\Diego\Nc_Tif\Inun_2_5_L 32718

import numpy as np
import rioxarray
import xarray as xr
import os

from osgeo import gdal
import glob

import sys

## INPUTS
input = ' '.join(sys.argv[1:]) # Input único

# EPSG de 5 dígitos
if input[-6]==' ':
    pm = str(input[0:-6]) # DIRECTORIO DONDE ESTÁ .NC
    region_epsg = input[-5::] # EPSG
    
# EPSG de 4 dígitos
else:
    pm = str(input[0:-5]) # DIRECTORIO DONDE ESTÁ .NC
    region_epsg = input[-4::] #EPSG


#MOISES

ds = xr.open_dataset(os.path.join(pm,'sfincs_map.nc'),mask_and_scale=True)

xx = sorted(np.unique(ds.x.data))
yy = sorted(np.unique(ds.y.data))
hmax = ds.hmax.data[0,:,:]
time = ds.timemax.data

if not len(xx)==hmax.shape[1]:
    da = xr.Dataset(data_vars=dict(
        hmax=(["y","x"], hmax.T),
    ),
    coords=dict(
        x=(["x"], xx),
        y=(["y"], yy),
    ),
    attrs=dict(description="Weather related data."),)
    da = da.rio.write_crs("EPSG:"+str(region_epsg))
else:
    da = xr.Dataset(data_vars=dict(
    hmax=(["y","x"], hmax),
    ),
    coords=dict(
        x=(["x"], xx),
        y=(["y"], yy),
    ),
    attrs=dict(description="Weather related data."),)
    da = da.rio.write_crs("EPSG:"+str(region_epsg))
	
da.to_netcdf(os.path.join(pm,'sfincs_map_hmax.nc'))
da.rio.to_raster(os.path.join(pm,r"sfincs_map_hmax.tif"))


#SARA

# Para guardar resultados
pout=pm+"\Rasters_inun_Recortados"

if not os.path.exists(pout):
    os.makedirs(pout)

data = pm

#Lista todos los .tiff del directorio
archivos_tif = glob.glob(os.path.join(data, '*.tif'))

for archivo in archivos_tif:
    print(archivo)
    nombre_archivo = os.path.splitext(os.path.basename(archivo))[0]
    print(nombre_archivo)

    name = str(nombre_archivo)
    output_raster = os.path.join(pout, name)

    try:
        # Abrir el archivo raster con GDAL
        dataset = gdal.Open(archivo, gdal.GA_ReadOnly)
        
        if dataset is None:
            raise Exception(f"No se pudo abrir el archivo: {archivo}")

        # Calcular las estadísticas del raster
        dataset.GetRasterBand(1).ComputeStatistics(False)

        # Obtener el valor mínimo
        minimo = dataset.GetRasterBand(1).GetMinimum()
        minimo = float(minimo)

        print(minimo)

        # Crear una copia del raster y establecer los valores iguales al mínimo a NULL
        driver = gdal.GetDriverByName("GTiff")
        out_dataset = driver.CreateCopy(output_raster + ".tif", dataset, 0)
        out_band = out_dataset.GetRasterBand(1)
        out_band.SetNoDataValue(minimo)
        out_band.FlushCache()

        # Cerrar los datasets
        dataset = None
        out_dataset = None

    except Exception as e:
        print(f"Error al procesar el archivo: {archivo}")
        print(str(e))