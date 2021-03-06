import time

import mxnet as mx
import mxnet.gluon as g
import numpy as np

# define hyperparameters
batch_size = 32
learning_rate = 1e-3
epochs = 100
step = 300
ctx = mx.gpu()


# define data transform
def data_transform(data, label):
    return data.astype(np.float32) / 255, label.astype(np.float32)


# define dataset and dataloader
train_dataset = g.data.vision.MNIST(transform=data_transform)
test_dataset = g.data.vision.MNIST(train=False, transform=data_transform)

train_loader = g.data.DataLoader(
    train_dataset, batch_size=batch_size, shuffle=True)
test_loader = g.data.DataLoader(
    test_dataset, batch_size=batch_size, shuffle=False)

# define model
logistic_model = g.nn.Sequential()
with logistic_model.name_scope():
    logistic_model.add(g.nn.Dense(10))

logistic_model.collect_params().initialize(
    mx.init.Xavier(rnd_type='gaussian'), ctx=ctx)

criterion = g.loss.SoftmaxCrossEntropyLoss()
optimizer = g.Trainer(logistic_model.collect_params(), 'sgd',
                      {'learning_rate': learning_rate})

# start train
for e in range(epochs):
    print('*' * 10)
    print('epoch {}'.format(e + 1))
    since = time.time()
    moving_loss = 0.0
    moving_acc = 0.0
    for i, (img, label) in enumerate(train_loader, 1):
        img = img.as_in_context(ctx).reshape((-1, 28 * 28))
        label = label.as_in_context(ctx)
        with g.autograd.record():
            output = logistic_model(img)
            loss = criterion(output, label)
        loss.backward()
        optimizer.step(img.shape[0])
        # =========== keep average loss and accuracy ==============
        moving_loss += mx.nd.mean(loss).asscalar()
        predict = mx.nd.argmax(output, axis=1)
        acc = mx.nd.mean(predict == label).asscalar()
        moving_acc += acc
        if i % step == 0:
            print('[{}/{}] Loss: {:.6f}, Acc: {:.6f}'.format(
                i, len(train_loader), moving_loss / step, moving_acc / step))
            moving_loss = 0.0
            moving_acc = 0.0
    test_loss = 0.0
    test_acc = 0.0
    total = 0.0
    for img, label in test_loader:
        img = img.as_in_context(ctx).reshape((-1, 28 * 28))
        label = label.as_in_context(ctx)
        output = logistic_model(img)
        loss = criterion(output, label)
        test_loss += mx.nd.sum(loss).asscalar()
        predict = mx.nd.argmax(output, axis=1)
        test_acc += mx.nd.sum(predict == label).asscalar()
        total += img.shape[0]
    print('Test Loss: {:.6f}, Test Acc: {:.6f}'.format(test_loss / total,
                                                       test_acc / total))
    print('Time: {:.1f} s'.format(time.time() - since))

logistic_model.save_params('./logistic.params')