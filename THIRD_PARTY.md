# External components and data

- Shilalekhya: https://github.com/ihdia/shilalekhya-binarization . MIT code, copyright2025 ihdia. Preserve the source LICENSE with any copied implementation. Local source/weights are not committed here.
- Public pretrained binarizer and EpiSAM weights: https://huggingface.co/keyfinder08/EpiSAM_Inscriptions_Project . Repository declares CC BY-SA4.0. The current application uses binarizer.pth; it does not use episam.pth.
- Public EpiSAM dataset: https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset . CC BY-SA4.0. Arnav Sharma, Pratyush Jena, Amal Joseph and Ravi Kiran Sarvadevabhatla. Source imagery acknowledged to The Mythic Society Bengaluru. Preserve attribution and share-alike terms for redistributed derived images: https://creativecommons.org/licenses/by-sa/4.0/ . Supplied citation is retained in outputs/EpiSAM_source_README.md.
- Torchvision ResNet18/ImageNet weights are used only in the recorded transfer experiment: https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html . No claim of historical-Kannada pretraining. Model/data terms are separate from library code licenses.

No restricted Akshara Bhandara corpus was accessed. Local original datasets with unresolved provenance are excluded from Git. No blanket project license overrides third-party licenses; a license for original project code has not yet been selected.
