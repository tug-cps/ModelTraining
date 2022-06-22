from ModelTraining.dataimport import DataImport
from ModelTraining.feature_engineering.featurecreators import CategoricalFeatures, CategoricalFeaturesDivider,\
    CyclicFeatures, CyclicFeaturesSampleTime
import matplotlib.pyplot as plt

if __name__ == "__main__":
    data = DataImport.load("../Configuration/DataImport/Resampled15min.json").import_data(
        "../../Data/AEE/Resampled15min")
    cyc_feats = CyclicFeatures()
    print(data.columns)
    data_tr = cyc_feats.transform(data)
    print(data_tr.columns)
    print(cyc_feats.get_additional_feat_names())
    cyc_feats_s = CyclicFeaturesSampleTime(sample_time=900)
    data_tr_s = cyc_feats_s.transform(data)

    plt.plot(data_tr['weekday_sin'][0:1000])
    plt.plot(data_tr['weekday_cos'][0:1000])
    plt.plot(data_tr_s['weekday_sin'][0:1000])
    plt.plot(data_tr_s['weekday_cos'][0:1000])
    plt.show()

    categorical_feats = CategoricalFeatures()
    data_c = categorical_feats.transform(data)
    plt.plot(data_c['mon'][0:1000])
    plt.plot(data_c['tue'][0:1000])
    plt.plot(data_c['wed'][0:1000])
    plt.show()
    print(categorical_feats.get_additional_feat_names())

    categorical_feats = CategoricalFeaturesDivider()
    data_cd = categorical_feats.transform(data)
    plt.plot(data_cd['hour_0'][0:100])
    plt.plot(data_cd['hour_2'][0:100])
    plt.plot(data_cd['hour_4'][0:100])
    plt.show()
    print(categorical_feats.get_additional_feat_names())
    print(data_cd.columns)