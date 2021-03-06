
import tensorflow as tf

from utils.sparse_molecular_dataset import SparseMolecularDataset
from utils.trainer import Trainer
from utils.utils import *

from models.vae import GraphVAEModel
from models import encoder_rgcn, decoder_adj

from optimizers.vae import GraphVAEOptimizer

runname = 'vae-test-6'
batch_dim = 128
la = 0.75
n_critic = 2
metric = 'validity,qed'
n_samples = 1000
z_dim = 8
epochs = 6
save_every = n_critic

# load dataset
data = SparseMolecularDataset()
data.load('../MolGAN-pytorch/data/qm9_5k.sparsedataset')
steps = (len(data) // batch_dim)


def reward(mols):
    rr = 1.
    for m in ('logp,sas,qed,unique' if metric == 'all' else metric).split(','):
        if m == 'np':
            rr *= MolecularMetrics.natural_product_scores(mols, norm=True)
        elif m == 'logp':
            rr *= MolecularMetrics.water_octanol_partition_coefficient_scores(mols, norm=True)
        elif m == 'sas':
            rr *= MolecularMetrics.synthetic_accessibility_score_scores(mols, norm=True)
        elif m == 'qed':
            rr *= MolecularMetrics.quantitative_estimation_druglikeness_scores(mols, norm=True)
        elif m == 'novelty':
            rr *= MolecularMetrics.novel_scores(mols, data)
        elif m == 'dc':
            rr *= MolecularMetrics.drugcandidate_scores(mols, data)
        elif m == 'unique':
            rr *= MolecularMetrics.unique_scores(mols)
        elif m == 'diversity':
            rr *= MolecularMetrics.diversity_scores(mols, data)
        elif m == 'validity':
            rr *= MolecularMetrics.valid_scores(mols)
        else:
            raise RuntimeError('{} is not defined as a metric'.format(m))

    return rr.reshape(-1, 1)


def train_fetch_dict(i, steps, epoch, epochs, min_epochs, model, optimizer, la):
    a = [optimizer.train_step_VAE] if i % n_critic == 0 else []
    b = [optimizer.train_step_V] if i % n_critic == 0 and la < 1 else []
    return a + b


def train_feed_dict(i, steps, epoch, epochs, min_epochs, model, optimizer, la, batch_dim):
    mols, _, _, a, x, _, f, _, _ = data.next_train_batch(batch_dim)
    embeddings = model.sample_z(batch_dim)

    if la < 1:

        if i % n_critic == 0:
            reward_r = reward(mols)

            n, e = session.run([model.nodes_gumbel_argmax, model.edges_gumbel_argmax],
                               feed_dict={model.training: False, model.embeddings: embeddings})
            n, e = np.argmax(n, axis=-1), np.argmax(e, axis=-1)
            mols = [data.matrices2mol(n_, e_, strict=True) for n_, e_ in zip(n, e)]

            reward_f = reward(mols)

            feed_dict = {model.edges_labels: a,
                         model.nodes_labels: x,
                         model.node_features: f,
                         model.embeddings: embeddings,
                         model.rewardR: reward_r,
                         model.rewardF: reward_f,
                         model.training: True,
                         optimizer.la: la if epoch > 0 else 1.0}

        else:
            feed_dict = {model.edges_labels: a,
                         model.nodes_labels: x,
                         model.node_features: f,
                         model.embeddings: embeddings,
                         model.training: True,
                         optimizer.la: la if epoch > 0 else 1.0}
    else:
        feed_dict = {model.edges_labels: a,
                     model.nodes_labels: x,
                     model.node_features: f,
                     model.embeddings: embeddings,
                     model.training: True,
                     optimizer.la: 1.0}

    return feed_dict


def eval_fetch_dict(i, epochs, min_epochs, model, optimizer):
    return {'loss VAE': optimizer.loss_VAE, 'loss RL': optimizer.loss_RL, 'loss V': optimizer.loss_V,
            'la': optimizer.la}


def eval_feed_dict(i, epochs, min_epochs, model, optimizer, la, batch_dim):
    mols, _, _, a, x, _, f, _, _ = data.next_validation_batch()
    embeddings = model.sample_z(a.shape[0])

    rewardR = reward(mols)

    n, e = session.run([model.nodes_gumbel_argmax, model.edges_gumbel_argmax],
                       feed_dict={model.training: False, model.embeddings: embeddings})
    n, e = np.argmax(n, axis=-1), np.argmax(e, axis=-1)
    mols = [data.matrices2mol(n_, e_, strict=True) for n_, e_ in zip(n, e)]

    rewardF = reward(mols)

    feed_dict = {model.edges_labels: a,
                 model.nodes_labels: x,
                 model.node_features: f,
                 model.embeddings: embeddings,
                 model.rewardR: rewardR,
                 model.rewardF: rewardF,
                 model.training: False,
                 optimizer.la: la}
    return feed_dict


def test_fetch_dict(model, optimizer):
    return {'loss VAE': optimizer.loss_VAE, 'loss RL': optimizer.loss_RL, 'loss V': optimizer.loss_V,
            'la': optimizer.la}


def test_feed_dict(model, optimizer, la, batch_dim):
    mols, _, _, a, x, _, f, _, _ = data.next_test_batch()
    embeddings = model.sample_z(a.shape[0])

    rewardR = reward(mols)

    n, e = session.run([model.nodes_gumbel_argmax, model.edges_gumbel_argmax],
                       feed_dict={model.training: False, model.embeddings: embeddings})
    n, e = np.argmax(n, axis=-1), np.argmax(e, axis=-1)
    mols = [data.matrices2mol(n_, e_, strict=True) for n_, e_ in zip(n, e)]

    rewardF = reward(mols)

    feed_dict = {model.edges_labels: a,
                 model.nodes_labels: x,
                 model.node_features: f,
                 model.embeddings: embeddings,
                 model.rewardR: rewardR,
                 model.rewardF: rewardF,
                 model.training: False,
                 optimizer.la: la}
    return feed_dict


def _eval_test_update(model, mols=False):
    if mols:
        return samples(data, model, session, model.sample_z(n_samples), sample=True, smiles=True)
    else:
        mols = samples(data, model, session, model.sample_z(n_samples), sample=True)
        m0, m1 = all_scores(mols, data, norm=True)
        m0 = {k: np.array(v)[np.nonzero(v)].mean() for k, v in m0.items()}
        m0.update(m1)
        return m0


# model
model = GraphVAEModel(vertexes=data.vertexes,
                      edges=data.bond_num_types,
                      nodes=data.atom_num_types,
                      features=data.features,
                      embedding_dim=z_dim,
                      encoder_units=((128, 64), 128, (128, 64)),
                      decoder_units=(128, 256, 512),
                      encoder=encoder_rgcn,
                      decoder=decoder_adj,
                      variational=True,
                      soft_gumbel_softmax=False,
                      hard_gumbel_softmax=False,
                      with_features=True)

# optimizer
optimizer = GraphVAEOptimizer(model, learning_rate=1e-3)

# session
session = tf.Session()
session.run(tf.global_variables_initializer())

# trainer
trainer = Trainer(model, optimizer, session, runname)

print('Parameters: {}'.format(np.sum([np.prod(e.shape) for e in session.run(tf.trainable_variables())])))

trainer.train(batch_dim=batch_dim,
              epochs=epochs,
              steps=steps,
              la=la,
              train_fetch_dict=train_fetch_dict,
              train_feed_dict=train_feed_dict,
              eval_fetch_dict=eval_fetch_dict,
              eval_feed_dict=eval_feed_dict,
              test_fetch_dict=test_fetch_dict,
              test_feed_dict=test_feed_dict,
              save_every=save_every,
              directory='../MolGAN_TF_exps/QM9_5k_lam_1',
              _eval_update=_eval_test_update,
              _test_update=_eval_test_update)
