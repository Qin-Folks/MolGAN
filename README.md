# MolGAN
Tensorflow implementation of MolGAN: An implicit generative model for small molecular graphs (https://arxiv.org/abs/1805.11973)





## Overview
This library contains a Tensorflow implementation of MolGAN: An implicit generative model for small molecular graphs as presented inb[[1]](#citation)(https://arxiv.org/abs/1805.11973).
## Dependencies

* **python>=3.6**
* **tensorflow>=1.7.0**: https://tensorflow.org
* **rdkit**: https://www.rdkit.org/
* **numpy**

## Structure
* [data](https://github.com/nicola-decao/MolGAN/tree/master/data): should contain your datasets. If you run `download_dataset.sh` the script will download the dataset used for the paper.
* [examples](https://github.com/nicola-decao/MolGAN/tree/master/examples): Example code for using the library within a Tensorflow project. **Disclaimer: there are the experiments for the paper**.
* [models](https://github.com/nicola-decao/MolGAN/tree/master/hyperspherical_vae/models): 
* [optimizers](https://github.com/nicola-decao/MolGAN/tree/master/optimizers):

## Usage
Please have a look into the [examples folder](https://github.com/nicola-decao/MolGAN/tree/master/examples).

Please cite [[1](#citation)] in your work when using this library in your experiments.

## Feedback
For questions and comments, feel free to contact [Nicola De Cao](mailto:nicola.decao@gmail.com).

## License
MIT

## Citation
```
[1] De Cao, N., and Kipf, T. (2018).MolGAN: An implicit generative 
model for small molecular graphs. ICML 2018 workshop on Theoretical
Foundations and Applications of Deep Generative Models.
```

BibTeX format:
```
@article{de2018molgan,
  title={{MolGAN: An implicit generative model for small
  molecular graphs}},
  author={De Cao, Nicola and Kipf, Thomas},
  journal={ICML 2018 workshop on Theoretical Foundations 
  and Applications of Deep Generative Models},
  year={2018}
}

```