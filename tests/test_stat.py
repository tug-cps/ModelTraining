from ModelTraining.dataimport import DataImport
from ModelTraining.feature_engineering.timebasedfeatures import StatisticalFeatures
import matplotlib.pyplot as plt

if __name__ == "__main__":
    data = DataImport.load("../Configuration/DataImport/Resampled15min.json").import_data(
        "../../Data/AEE/Resampled15min")
    stat_feats = StatisticalFeatures(window_size=24)
    import datetime
    print(datetime.datetime.now())
    data_stat = stat_feats.fit_transform(data[['TSolarRL','VDSolar']])
    print(datetime.datetime.now())

    plt.figure()
    plt.plot(data['TSolarRL'][0:1000])
    plt.plot(data_stat['TSolarRL_tmin_24'][0:1000])
    plt.show()
    plt.figure()
    plt.plot(data['VDSolar'][0:1000])
    plt.plot(data_stat['VDSolar_tmin_24'][0:1000])
    plt.show()