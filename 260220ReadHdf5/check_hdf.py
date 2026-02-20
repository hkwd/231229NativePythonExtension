import h5py

f = h5py.File('c:/temp6/sample_sensor_data.h5', 'r')
print('Groups:', list(f.keys()))

if 'sensor_data' in f:
    print('\nsensor_data contents:', list(f['sensor_data'].keys()))
    for name in f['sensor_data'].keys():
        dataset = f['sensor_data'][name]
        print(f'\n{name}:')
        print(f'  shape: {dataset.shape}')
        print(f'  dtype: {dataset.dtype}')

f.close()

# Made with Bob
