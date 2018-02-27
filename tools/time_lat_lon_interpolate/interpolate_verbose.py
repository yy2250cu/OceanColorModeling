import pandas as pd
import xarray as xr
import numpy as np


def sel_points_multilinear(dset, dframe, dims='points', col_name = 'str'): 
    # col_name should match the satellite dataset
    '''    
    sel_points_multilinear(ds_9day, row_case1, dims = 'points', col_name ='chlor_a')
    
    function for generating multilinear interpolations in python
    
    input:  dset      xarray.dataset; the dictionary of values 
            dframe    pandas.dataframe; the lists {time, lat, lon, id}
            dims      default to be "Points" of xarray.dataset
            col_name  the variable to interpolate;
       
    #output: dframe_out       
    '''


    '''
    ### code piece for Trilinear interpolation
    # 1D
    w = delta_x / (x_next -x_nearest)
    f = (1-w)*da.isel(x=ix_nearest).values + w* da.isel(x=ix_next).values

    # 2D
    wx = delta_x / (x_next - x_nearest)
    wy = delta_y / (y_next - y_nearest)
    f = (1-wx)*(1-wy)*da.isel(x=ix_nearest, y=iy_nearest).values +
            (1-wx)*wy*da.isel(x=ix_nearest,y=iy_next).values     +
           wx*(1-wy)*da.isel(x=ix_next,y=iy_nearest).values     +
               wx*wy*da.isel(x=ix_next,y=iy_next).values

    # 3D
    ### interpolate the Trilinear Value
    dimensions 3 : time, lat, lon
    locations: xtime_test, xlat_test, xlon_test
    weights(from the nearest coordinates): w_time, w_lat, w_lon
    output: a singel value based on 1D interpolation on each dimension, so use 8-neighbours

    wx = delta_x / (x_next - x_nearest)
    wy = delta_y / (y_next - y_nearest)
    wz = delta_z / (z_next - z_nearest)
    f = (1-wx)*(1-wy)*(1-wz)*da.isel(x=ix_nearest, y=iy_nearest, z=iz_nearest).values  +
            (1-wx)*(1-wy)*wz*da.isel(x=ix_nearest, y=iy_nearest, z=iz_next).values     +
            (1-wx)*wy*(1-wz)*da.isel(x=ix_nearest, y=iy_next, z=iz_nearest).values     +
                (1-wx)*wy*wz*da.isel(x=ix_nearest, y=iy_next, z=iz_next).values        +
            wx*(1-wy)*(1-wz)*da.isel(x=ix_next, y=iy_nearest, z=iz_nearest).values     +
                wx*(1-wy)*wz*da.isel(x=ix_next, y=iy_nearest, z=iz_next).values        +
                wx*wy*(1-wz)*da.isel(x=ix_next, y=iy_next, z=iz_nearest).values        +
                    wx*wy*wz*da.isel(x=ix_next, y=iy_next, z=iz_next).values
    '''

    ###
    eps_float32 = np.finfo(np.float32).eps   # selection on the nearest point will reduce accuracy!

    ## get the indices of time, lat, lon
    idx_time = dset.indexes['time'] 
    idx_lat = dset.indexes['lat']
    idx_lon = dset.indexes['lon']



    ##  bounds
    '''
    # row_case.lat > ds_9day.lat.min  # descending
    # row_case.lat < ds_9day.lat.max  # descending
    # row_case.lon > ds_9day.lat.min  # ascending
    # row_case.lat > ds_9day.lat.min  # ascending
    '''
    dset_latmin = dset.lat.to_series().min()
    dset_latmax = dset.lat.to_series().max()

    dset_lonmin = dset.lon.to_series().min()
    dset_lonmax = dset.lon.to_series().max()

    mask = (dframe.lat > dset_latmin) & (dframe.lat < dset_latmax)
    mask = mask & (dframe.lon > dset_lonmin) & (dframe.lon < dset_lonmax)

    dframe = dframe[mask]
    '''
    ################### printings
    ### 'time is from small to big number'
    print(dset.indexes['time'])
    print(type(dset.indexes['time']))

    ### 'lat is from *big* to small number'
    print(dset.indexes['lat'])
    print(type(dset.indexes['lat']))

    ### 'lon is from small to big number'
    print(dset.indexes['lon'])
    print(type(dset.indexes['lon']))

    # validation: to locate the chl-a for this point 
    #{time:2002-07-13, lat:27.7916660309, lon:45.2916679382}
    '''
    
    #### 
    #interpolation on the time dimension
    time_len = len(dframe.time.values)
    xtime_test = list([ np.datetime64(dframe.time.values[i]) 
                 for i in range(0,time_len)  ] )  # for delta 
    print('\n xtime_test \n', xtime_test)

    '''caution: cannot do this inside the function get_loc,
    see https://github.com/pandas-dev/pandas/issues/3488
    '''
    itime_nearest = [idx_time.get_loc(xtime_test[i], method='nearest') 
                     for i in range(0, time_len)]
    print('\n itime_nearest \n', itime_nearest)  # [1,2]

    xtime_nearest =  dset.time[itime_nearest].values  
    #  ['2002-07-13T00:00:00.000000000' '2002-07-22T00:00:00.000000000']
    print('\n xtime_nearest\n', xtime_nearest)
    # ['2002-07-13T00:00:00.000000000' '2002-07-22T00:00:00.000000000']
    print('xtime_nearest', type(xtime_nearest))
    # xtime_nearest <class 'numpy.ndarray'> # time_nearest <class 'numpy.datetime64'>

    # the time distance in days
    delta_xtime = (xtime_test - xtime_nearest) / np.timedelta64(1, 'D')
    print('\n delta_xtime in days \n', delta_xtime)
    print(type(delta_xtime))

    itime_next = [itime_nearest[i]+1 if delta_xtime[i] >=0
                                     else itime_nearest[i]-1
                                     for i in range(0, time_len) ]
    print('\n itime_next \n',itime_next)  # [2, 3]

    # find the next coordinate values
    xtime_next = dset.time[itime_next].values
    print('\n xtime_next \n', xtime_next)
    # ['2002-07-22T00:00:00.000000000' '2002-07-31T00:00:00.000000000']

    # prepare for the Tri-linear interpolation
    base_time = (xtime_next - xtime_nearest) / np.timedelta64(1, 'D')  
    # [ 9.  9.]
    print('\n base_time \n', base_time)
    w_time = delta_xtime / base_time  
    print('\n w_time \n', w_time) # [ 0.  0.]


    #### 
    #interpolation on the lat dimension
    #xlat_test = dframe.lat.values + 0.06  
    # base [ 5.20833349  5.29166174] 
    # cell distance around .8, use .2 & .6 as two tests
    xlat_test = dframe.lat.values
    print('\n xlat_test \n', xlat_test)
    # xlat_test [ 5.26833349  5.35166174]
    
    ilat_nearest = [idx_lat.get_loc(xlat_test[i], method='nearest') 
                    for i in range(0, time_len)]
    print('\n ilat_nearest \n', ilat_nearest) # [272, 271]

    xlat_nearest = dset.lat[ilat_nearest].values  
    print('\n xlat_nearest \n', xlat_nearest) # [ 5.29166174  5.37499762]

    delta_xlat = xlat_test - xlat_nearest
    print("\n delta_xlat \n",delta_xlat)      #  [-0.02332825 -0.02333588]


    # the nearest index is on the right; but order of the latitude is different, it is descending
    # delta_xlat[i] is of type float64
    ilat_next = [ilat_nearest[i]-1 if delta_xlat[i] >= (-1.0 *eps_float32)
                 else ilat_nearest[i]+1  
                 for i in range(0, time_len) ]
    print('\n ilat_next \n', ilat_next)  # [273, 272]

    # find the next coordinates value
    xlat_next = dset.lat[ilat_next].values
    print('\n xlat_next \n', xlat_next)  # [ 5.20833349  5.29166174]

    # prepare for the Tri-linear interpolation
    w_lat = delta_xlat / (xlat_next - xlat_nearest)
    print('\n w_lat \n', w_lat) # [ 0.27995605  0.28002197]

    #### 
    #interpolation on the lon dimension
    #xlon_test = dframe.lon.values +0.06
    # base [74.7083358765, 74.6250076294] 
    # cell distance around .8, use .2 & .6 as two tests
    xlon_test = dframe.lon.values
    print('\n xlon_test \n', xlon_test)  # [ 74.76833588  74.68500763]

    ilon_nearest = [idx_lon.get_loc(xlon_test[i], method='nearest') 
                    for i in range(0, time_len)]
    print('\n ilon_nearest \n', ilon_nearest) # [357, 356]

    xlon_nearest = dset.lon[ilon_nearest].values  
    print('\n xlon_nearest \n', xlon_nearest) # [ 74.79166412  74.70833588]

    delta_xlon = xlon_test - xlon_nearest     
    print("\n delta_xlon \n", delta_xlon)     #  [-0.02332825 -0.02332825]

    ilon_next = [ilon_nearest[i]+1 if delta_xlon[i] >= (1.0 *eps_float32)
                 else ilon_nearest[i]-1  
                 for i in range(0, time_len) ]
    print('\n ilon_next \n',ilon_next)  # [356, 355]

    # find the next coordinate values
    xlon_next = dset.lon[ilon_next].values
    print("\n xlon_next \n", xlon_next) # [ 74.70833588  74.62500763]

    # prepare for the Tri-linear interpolation
    w_lon = delta_xlon / (xlon_next - xlon_nearest)
    print("\n w_lon \n", w_lon) # [ 0.27995605  0.27995605]

    ####
    # local Tensor product for Trilinear interpolation
    # caution: nan values, store as "list_of_array to 2d_array" first, then sum

    # no casting to list needed here, inputs are already lists
    tmp = np.array([
             dset[col_name].isel_points(time=itime_nearest, lat=ilat_nearest, lon=ilon_nearest).values,
             dset[col_name].isel_points(time=itime_nearest, lat=ilat_nearest, lon=ilon_next).values,
             dset[col_name].isel_points(time=itime_nearest, lat=ilat_next, lon=ilon_nearest).values,
             dset[col_name].isel_points(time=itime_nearest, lat=ilat_next, lon=ilon_next).values,
             dset[col_name].isel_points(time=itime_next, lat=ilat_nearest, lon=ilon_nearest).values,
             dset[col_name].isel_points(time=itime_next, lat=ilat_nearest, lon=ilon_next).values,
             dset[col_name].isel_points(time=itime_next, lat=ilat_next, lon=ilon_nearest).values,
             dset[col_name].isel_points(time=itime_next, lat=ilat_next, lon=ilon_next).values ])

    weights = np.array([(1-w_time)*(1-w_lat)*(1-w_lon),
                        (1-w_time)*(1-w_lat)*w_lon,
                        (1-w_time)*w_lat*(1-w_lon),
                        (1-w_time)*w_lat*w_lon,
                         w_time*(1-w_lat)*(1-w_lon),
                         w_time*(1-w_lat)*w_lon,
                         w_time*w_lat*(1-w_lon),
                         w_time*w_lat*w_lon ])


    # how to deal with "nan" values, fill in missing values for the np.array tmpAll 
    # or fill the mean values to the unweighted array
    # http://stackoverflow.com/questions/18689235/numpy-array-replace-nan-values-with-average-of-columns

    print('\n neighbouring tensor used \n', tmp)
    '''
     neighbouring tensor used 
     [[        nan  0.181841  ]
     [ 0.245878           nan]
     [        nan         nan]
     [        nan         nan]
     [ 0.19680101         nan]
     [        nan         nan]
     [        nan         nan]
     [ 0.18532801         nan]]
    '''

    # column min: (nan+0.245878 + nan + nan + 0.19680101 + nan +  nan + 0.18532801)/8 = 0.20933567333
    col_mean = np.nanmean(tmp, axis=0)
    print('\n its mean along axis 0(column) \n', col_mean)  #  [ 0.20933567  0.181841  ]


    # filling the missing values.
    inds = np.where(np.isnan(tmp))
    print('\n nan index\n', inds)
    tmp[inds]=np.take(col_mean, inds[1])
    print('\n values after the fill \n', tmp)

    print('\n weighting tensor used \n', weights)

    print("weights.shape", weights.shape) # (8, 3)
    print("tmp.shape", tmp.shape)  # (8, 3)

    nrow_w, ncol_w = weights.shape
    nrow_t, ncol_t = tmp.shape
    assert nrow_w == nrow_t, "the row count of weights and values are not the same!"
    assert ncol_w == ncol_t, "the row count of weights and values are not the same!"
    print('\n tensor product\n', np.dot(weights[:,0], tmp[:,0]) ) # 0.216701896135 should be [ 0.2167019]

    # new interpolation process of the Chl_a
    chl_new = np.empty(ncol_w)
    for i in range(0, ncol_w, 1):
        chl_new[i] =  np.dot(weights[:,i], tmp[:,i])

    print('chl_newInt',  chl_new) #  [ 0.2167019  0.181841   0.2167019]
    # validate by 1D array
    # val = np.array([0.20933567, 0.245878,  0.20933567,
    #                0.20933567, 0.19680101, 0.20933567,
    #               0.20933567,0.18532801]) 
    # np.dot(val, weights) # 0.21670189702309739


    ## output xarray.dataarray of points, see examples below
    # this is the way how xarray.Dataset works
    # if you want a xarray.DataArray, first generate a xarray.Dataset, then select DataArray from there.
    dframe_out = xr.Dataset({col_name: (['points'],chl_new)},
                            coords={
    #'time':(['points'],['2002-07-13 00:00:00', '2002-07-22 00:00:00', '2002-07-13 00:00:00']) ,
                                    'time':(['points'], dframe.time) ,
                                    'id': (['points'], dframe.id), 
                                    'lon': (['points'], dframe.lon),
                                    'lat':(['points'], dframe.lat), 
                                    'points': (['points'], range(0,len(dframe))) } ) # dims is set to point

    print('\n', dframe_out[col_name])
   
    ## summation
    print('\n dset \n', dset)
    print('\n dims \n', dims)
    #print('\n time is \n', time)
    #print('\n lat is \n', lat )
    #print('\n lon is \n', lon )
    
    return dframe_out
    
#newtmpAll = sel_points_multilinear(ds_9day, dims = 'points', out ='chlor_a', 
#time = list(['2002-07-13 00:00:00']), lat = list([5]),  lon = list([70]) )
    

################
##test case 1-4
##### xlat_test = dframe.lat.values + 0.06
#####  xlon_test = dframe.lon.values +0.06


## test case 1: take a single entry (southeast corner for valid values) (passed)
#row_case1 =  pd.DataFrame(data = {'time':'2002-07-13 00:00:00', 'id': 10206,
#                                  'lon':74.7083358765, 'lat':5.20833349228},index=[1])
##print(row_case1)
#ds_9day = xr.open_dataset("./ds_9day.nc")
#result_out1 = sel_points_multilinear(ds_9day, row_case1, dims = 'points', col_name ='chlor_a')  # + 0.06 for both
##print(result_out1)
#recheck the [id], [index], [] & there length in the output


## test case 2: take 3 entries (passed):
#row_case2 =  pd.DataFrame(data = {'time':['2002-07-13 00:00:00', '2002-07-22 00:00:00', '2002-07-13 00:00:00'] ,
#                           'id': [10206, 10206, 10206], 'lon':[74.7083358765, 74.6250076294,74.7083358765],
#                            'lat':[5.20833349228, 5.29166173935, 5.20833349228]}, index=[1,2,3])
##print(row_case2)
#ds_9day = xr.open_dataset("./ds_9day.nc")
#result_out2 = sel_points_multilinear(ds_9day, row_case2, dims = 'points', col_name ='chlor_a')
#print(result_out2)


## test case 3: use the partial real data
# row_case3 = pd.DataFrame(data={'time':list(floatsDFAll_9Dtimeorder.time[:15]),
#                                'lon':list(floatsDFAll_9Dtimeorder.lon[:15]),
#                                'lat':list(floatsDFAll_9Dtimeorder.lat[:15]),
#                                'id':list(floatsDFAll_9Dtimeorder.id[:15]) } )
# print('\n before dropping nan \n', row_case3)
## process to drop nan in any of the columns [id], [lat], [lon], [time]
# row_case3 = row_case3.dropna(subset=['id', 'lat', 'lon', 'time'], how = 'any') # these four fields are critical
# print('\n after dropping nan \n', row_case3)
# result_out3 = sel_points_multilinear(ds_9day, row_case3, dims = 'points', col_name ='chlor_a')
# print('\n after the preprocessing \n', result_out3)
# print('\n this two length should be equal %d == %d?' %(len(row_case3.index), len(result_out3.points) ) )



## test case 4: using the real data
#row_case4 = pd.read_csv("./row_case4.csv")
#ds_9day = xr.open_dataset("./ds_9day.nc")
# bounds
## row_case.lat > ds_9day.lat.min  # descending
## row_case.lat < ds_9day.lat.max  # descending
## row_case.lon > ds_9day.lat.min  # ascending
## row_case.lat > ds_9day.lat.min  # ascending
#result_out4 = sel_points_multilinear(ds_9day, row_case4, dims = 'points', col_name ='chlor_a')
#print('\n after the preprocessing \n', result_out4)
#print('\n this two length should be equal %d >= %d?' %(len(row_case4.index), len(result_out4.points) ) )



#tasks:
# c. check the interface and may need to take the id and index from the float data, decide where to dropna, 
#    perhaps before the functions calls
# d. need to remove or comment out the print outs


# tmpAll = ds_9day.chlor_a.sel_points(time=list(floatsDFAll_9Dtimeorder.time),
#                                     lon=list(floatsDFAll_9Dtimeorder.lon),
#                                     lat=list(floatsDFAll_9Dtimeorder.lat),
#                                     method='nearest')