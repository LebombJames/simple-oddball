import os
import time

import mne
import mne_bids
import neurokit2 as nk
import numpy as np
import pandas as pd

# Preprocess physio ========================================================

# Convenience functions ----------------------------------------------------
def load_xdf(ppt):
    df, info = nk.read_xdf(
        filename="./data/" + ppt, fillmissing=1
    )

    df = df.reset_index()

    # df = df.rename(
    #     columns={
    #         "PPG": "PPG_Muse",
    #         "IR": "PPG_Muse",
    #         "RESPBIT0": "RSP",
    #         "ECGBIT1": "ECG",
    #         "PULSEOXI2": "PPG",
    #         "PULSEOXI3": "PPG",
    #         "LUX2": "PHOTO",
    #     }
    # )

    # Select channels
    # df = df[
    #     [
    #         "TP9",
    #         "AF7",
    #         "AF8",
    #         "TP10",
    #         "PPG_Muse",
    #         "GYRO",
    #         "ACC",
    #         "ECG",
    #         "RSP",
    #         "PHOTO",
    #     ]
    # ]

    return df, info

out = pd.DataFrame()

def save_bids(ppt):
    # Save BIDS
    bids_path = mne_bids.BIDSPath(
        subject="001",
        session=None,
        run="001",
        datatype="eeg",
        root=path,
        task="oddball",
    )

    # If file exist
    if os.path.exists(bids_path):
        print("  - skipping.")
        return None

    # Load XDF
    read = False
    while not read:
        try:
            df, _ = load_xdf(ppt=ppt)
            read = True
        except OSError as e:
            time.sleep(1)  # waiting for file to be released...
            print(e)

    if "LUX2" not in df.columns:
        return

    # Create metadata
    ch_eeg = ["TP9", "AF7", "AF8", "TP10"]
    ch_misc = ["LUX2"]

    # Rescale EEG
    df[["TP9", "AF7", "AF8", "TP10"]] = df[["TP9", "AF7", "AF8", "TP10"]] * 1e-6

    info = mne.create_info(
        ch_names=ch_eeg + ch_misc,
        ch_types=["eeg"] * len(ch_eeg) + ["misc"] * len(ch_misc),
        sfreq=2000,
    )

    info.set_montage("standard_1020")
    raw = mne.io.RawArray(df[ch_eeg + ch_misc].T, info, verbose=False)

    events = nk.events_find(
        df["LUX2"],  # nk.signal_plot(rs["PHOTO"][0][0])
        threshold_keep="below",
        # duration_min=int(info["sfreq"] * 5),
    )

    events, _ = nk.events_to_mne(events)

    epochs = mne.Epochs(
        raw,
        events,
        tmin=-0.50, # 0 is the sound onset. The Lux is black for 1500ms, followed by a fixation cross for 500ms
        tmax=1.50,
        detrend=None,
        decim=20,  # Downsample to 100 Hz
        verbose=True,
        preload=True,
    )
    # Remove epochs with missing data
    epochs = epochs.drop([np.isnan(e).any() for e in epochs])

    epochs_df = epochs.copy().to_data_frame()

    epochs_df["participant_id"] = ppt

    global out
    out = pd.concat([out, epochs_df])

    # mne_bids.write_raw_bids(
    #     raw=raw,
    #     events=events,
    #     bids_path=bids_path,
    #     allow_preload=True,
    #     format="BrainVision",
    #     overwrite=True,
    #     verbose=0,
    # )



# Save BIDS ----------------------------------------------------------------
for ppt in os.listdir("./data/"):
    save_bids(ppt)
out.to_csv('out.csv', index=False, columns=("time", "TP9", "TP10", "AF7", "AF8","LUX2", "epoch", "participant_id"))
print("Physio Done!")
