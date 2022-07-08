import os
import glob
import numpy as np
import pandas as pd
from EEGProcessing import (
    load_data,
    extract_sleep_stages,
    load_pre_split_data,
    power_spectral_density,
    sample_entropy,
    spectral_entropy,
    compute_dfa,
    fooof_1_over_f,
    compute_lziv,
)

# caffeine dose: 200 or 400
CAF_DOSE = 200
# path to the subject information CSV file
SUBJECTS_PATH = f"data/CAF_{CAF_DOSE}_Inventaire.csv"
# directory with the raw EEG data
DATA_PATH = f"data/raw_eeg{CAF_DOSE}"
# directory where features will be stored
FEATURES_PATH = f"data/Features{CAF_DOSE}"
# if True, use a hypnogram to split the raw EEG data into sleep stages
# if False, load data that is already split into sleep stages
SPLIT_STAGES = False

# which features to compute
psd = True
sampEn = True
specShanEn = True
specSampEn = True
dfa = True
oneOverF = True
lziv = True


def save_feature_dict(name, folder_path, feature_dict):
    folder_path = os.path.join(folder_path, name)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    for key, feature in feature_dict.items():
        path = os.path.join(folder_path, f"{name}_{key}")
        np.save(path, feature)


def create_folder(name, folder_path):
    folder_path = os.path.join(folder_path, name)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)


subject_ids = pd.read_csv(SUBJECTS_PATH, index_col=0)["Subject_id"]

done_subjects = []
while len(subject_ids) > len(done_subjects):
    psd_done = False
    sampEn_done = False
    specShanEn_done = False
    specSampEn_done = False
    dfa_done = False
    oneOverF_done = False
    lziv_done = False

    subject_id = subject_ids.iloc[0]
    i = 1
    while subject_id in done_subjects:
        if i >= len(subject_ids):
            break
        subject_id = subject_ids.iloc[i]
        i += 1

    subject_path = os.path.join(FEATURES_PATH, subject_id)
    print(
        f"----------------------------- NEW SUBJECT: {subject_id} -----------------------------"
    )
    done_subjects.append(subject_id)
    if not os.path.exists(subject_path):
        print(f"Creating feature folder for subject '{subject_id}'...", end="")
        os.mkdir(subject_path)
        if psd:
            create_folder("PSD", subject_path)
        if sampEn:
            create_folder("SampEn", subject_path)
        if specShanEn:
            create_folder("SpecShanEn", subject_path)
        if specSampEn:
            create_folder("SpecSampEn", subject_path)
        if dfa:
            create_folder("DFA", subject_path)
        if oneOverF:
            create_folder("OneOverF", subject_path)
        if lziv:
            create_folder("LZiv", subject_path)
        print("done")
    else:
        features = [
            file.split(os.sep)[-1]
            for file in glob.glob(os.path.join(subject_path, "*"))
        ]
        finished = True
        if psd:
            if "PSD" in features:
                psd_done = True
            else:
                finished = False
                create_folder("PSD", subject_path)
        if sampEn:
            if "SampEn" in features:
                sampEn_done = True
            else:
                finished = False
                create_folder("SampEn", subject_path)
        if specShanEn:
            if "SpecShanEn" in features:
                specShanEn_done = True
            else:
                finished = False
                create_folder("SpecShanEn", subject_path)
        if specSampEn:
            if "SpecSampEn" in features:
                specSampEn_done = True
            else:
                finished = False
                create_folder("SpecSampEn", subject_path)
        if dfa:
            if "DFA" in features:
                dfa_done = True
            else:
                finished = False
                create_folder("DFA", subject_path)
        if oneOverF:
            if "OneOverF" in features:
                oneOverF_done = True
            else:
                finished = False
                create_folder("OneOverF", subject_path)
        if lziv:
            if "LZiv" in features:
                lziv_done = True
            else:
                finished = False
                create_folder("LZiv", subject_path)

        if finished:
            print("Features already computed, moving on.")
            continue

    if SPLIT_STAGES:
        eeg_path = os.path.join(DATA_PATH, subject_id, "EEG_data_clean.npy")
        assert os.path.exists(eeg_path), (
            f"Raw EEG data was not found at {eeg_path}. "
            "Make sure it exists or switch SPLIT_STAGES to False."
        )
        hyp_path = os.path.join(DATA_PATH, subject_id, "hyp_clean.npy")
        assert os.path.exists(hyp_path), (
            f"Hypnogram data was not found at {hyp_path}. "
            "Make sure it exists or switch SPLIT_STAGES to False."
        )
        print("Loading EEG and sleep hypnogram data...", end="", flush=True)
        eeg_data, hyp_data = load_data(eeg_path, hyp_path)
        print("done")

        print("Extracting sleep stages...", end="", flush=True)
        stages = extract_sleep_stages(eeg_data, hyp_data)
        del eeg_data, hyp_data
        print("done")
    else:
        print(
            "SPLIT_STAGES is set to False. Loading data that is already split into sleep stages...",
            end="",
            flush=True,
        )
        stages = load_pre_split_data(DATA_PATH, subject_id)
        print("done")

    if psd and not psd_done:
        feature = {}
        print("Computing power spectral density...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = power_spectral_density(stage)
        save_feature_dict("PSD", subject_path, feature)
        print("done")

    if sampEn and not sampEn_done:
        feature = {}
        print("Computing sample entropy...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = np.empty((stage.shape[0], stage.shape[2]))
            for elec in range(stage.shape[0]):
                for epoch in range(stage.shape[2]):
                    feature[key][elec, epoch] = sample_entropy(stage[elec, :, epoch])
        save_feature_dict("SampEn", subject_path, feature)
        print("done")

    if specShanEn and not specShanEn_done:
        feature = {}
        print("Computing spectral shannon entropy...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = spectral_entropy(stage, method="shannon")
        save_feature_dict("SpecShanEn", subject_path, feature)
        print("done")

    if specSampEn and not specSampEn_done:
        feature = {}
        print("Computing spectral sample entropy...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = spectral_entropy(stage, method="sample")
        save_feature_dict("SpecSampEn", subject_path, feature)
        print("done")

    if dfa and not dfa_done:
        feature = {}
        print("Computing DFA...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = compute_dfa(stage)
        save_feature_dict("DFA", subject_path, feature)
        print("done")

    if oneOverF and not oneOverF_done:
        feature = {}
        print("Computing 1/f...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = fooof_1_over_f(stage)
        save_feature_dict("OneOverF", subject_path, feature)
        print("done")

    if lziv and not lziv_done:
        feature = {}
        print("Computing Lempel-Ziv complexity...", end="", flush=True)
        for key, stage in stages.items():
            feature[key] = compute_lziv(stage)
        save_feature_dict("LZiv", subject_path, feature)
        print("done")
