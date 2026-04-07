"""Label maps: dataset folder names ↔ UI copy ↔ short clinical codes (API)."""

# Folder names under dataset/
CLASS_TO_UI_STAGE = {
    "NonDemented": "Normal",
    "VeryMildDemented": "Very Mild Impairment",
    "MildDemented": "Mild Cognitive Impairment",
    "ModerateDemented": "Alzheimer's Disease",
}

# Short codes for `prediction` field (CN = cognitively normal, etc.)
CLASS_TO_SHORT = {
    "NonDemented": "CN",
    "VeryMildDemented": "VMCI",
    "MildDemented": "MCI",
    "ModerateDemented": "AD",
}

UI_STAGE_TO_SHORT = {
    "Normal": "CN",
    "Very Mild Impairment": "VMCI",
    "Mild Cognitive Impairment": "MCI",
    "Alzheimer's Disease": "AD",
}

UI_EXPLANATIONS = {
    "Normal": "No significant markers of cognitive decline were detected in this scan.",
    "Very Mild Impairment": "The scan shows early signs of neurodegeneration. Follow-up clinical evaluation is recommended.",
    "Mild Cognitive Impairment": "The scan shows early signs of neurodegeneration. Follow-up clinical evaluation is recommended.",
    "Alzheimer's Disease": "The scan shows significant hippocampal atrophy and cortical thinning consistent with Alzheimer's Disease.",
}
