# SPSS Modeler 拡張入力ノード - HDF5ファイル読み込み
# HDFファイルからsensor_dataグループのデータを読み込む

import modelerpy
import h5py
import pandas as pd
import numpy as np

# HDFファイルのパス
HDF_FILE_PATH = r'c:\temp6\sample_sensor_data.h5'
GROUP_NAME = 'sensor_data'

if modelerpy.isComputeDataModelOnly():
    # データモデルのみを計算する場合
    # HDFファイルを開いてメタデータを取得
    with h5py.File(HDF_FILE_PATH, 'r') as hdf_file:
        if GROUP_NAME not in hdf_file:
            raise ValueError(f"グループ '{GROUP_NAME}' がHDFファイルに見つかりません")

        group = hdf_file[GROUP_NAME]

        # 出力データモデルを構築
        outputDataModel = modelerpy.DataModel([])

        # グループ内の各データセットをフィールドとして追加
        for dataset_name in group.keys():
            dataset = group[dataset_name]
            dtype = dataset.dtype

            # データ型に基づいてストレージタイプと測定タイプを決定
            if dtype == np.float64 or dtype == np.float32:
                storage_type = 'real'
                measure_type = 'continuous'
            elif dtype == np.int64 or dtype == np.int32 or dtype == np.int16 or dtype == np.int8:
                storage_type = 'integer'
                measure_type = 'continuous'
            elif dtype == object or dtype.kind == 'S':
                storage_type = 'string'
                measure_type = 'nominal'
            else:
                # その他の型はデフォルトで文字列として扱う
                storage_type = 'string'
                measure_type = 'nominal'

            # フィールドを追加
            outputDataModel.addField(
                modelerpy.Field(dataset_name, storage_type, measure_type)
            )

    # 出力データモデルを設定
    modelerpy.setOutputDataModel(outputDataModel)

else:
    # 実際のデータを計算する場合
    # HDFファイルを開いてデータを読み込む
    with h5py.File(HDF_FILE_PATH, 'r') as hdf_file:
        if GROUP_NAME not in hdf_file:
            raise ValueError(f"グループ '{GROUP_NAME}' がHDFファイルに見つかりません")

        group = hdf_file[GROUP_NAME]

        # データを辞書に格納
        data_dict = {}
        for dataset_name in group.keys():
            dataset = group[dataset_name]

            # データを読み込む
            data = dataset[:]

            # オブジェクト型の場合、バイト列を文字列にデコード
            if dataset.dtype == object:
                try:
                    data = np.array([item.decode('utf-8') if isinstance(item, bytes) else str(item) for item in data])
                except:
                    data = np.array([str(item) for item in data])

            data_dict[dataset_name] = data

        # Pandas DataFrameを作成
        outputData = pd.DataFrame(data_dict)

    # データをSPSS Modelerに書き込む
    modelerpy.writePandasDataframe(outputData)

# Made with Bob
