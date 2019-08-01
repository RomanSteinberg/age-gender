import tensorflow as tf

from tensorflow.python.framework import ops
from tensorflow.python.ops import math_ops
from tensorflow.python.eager import context

def cyclic_learning_rate(global_step,
                         learning_rate=0.01,
                         max_lr=0.1,
                         step_size=20.,
                         gamma=0.99994,
                         mode='triangular',
                         name=None):
    if global_step is None:
        raise ValueError("global_step is required for cyclic_learning_rate.")
    with ops.name_scope(name, "CyclicLearningRate",
                        [learning_rate, global_step]) as name:
        learning_rate = ops.convert_to_tensor(learning_rate, name="learning_rate")
        dtype = learning_rate.dtype
        global_step = math_ops.cast(global_step, dtype)
        step_size = math_ops.cast(step_size, dtype)

        def cyclic_lr():
            double_step = math_ops.multiply(2., step_size)
            global_div_double_step = math_ops.divide(global_step, double_step)
            cycle = math_ops.floor(math_ops.add(1., global_div_double_step))
            double_cycle = math_ops.multiply(2., cycle)
            global_div_step = math_ops.divide(global_step, step_size)
            tmp = math_ops.subtract(global_div_step, double_cycle)
            x = math_ops.abs(math_ops.add(1., tmp))
            a1 = math_ops.maximum(0., math_ops.subtract(1., x))
            a2 = math_ops.subtract(max_lr, learning_rate)
            clr = math_ops.multiply(a1, a2)
            if mode == 'triangular2':
                clr = math_ops.divide(clr, math_ops.cast(math_ops.pow(2, math_ops.cast(
                    cycle - 1, tf.int32)), tf.float32))
            if mode == 'exp_range':
                clr = math_ops.multiply(math_ops.pow(gamma, global_step), clr)
            return math_ops.add(clr, learning_rate, name=name)

        if not context.executing_eagerly():
            cyclic_lr = cyclic_lr()
        return cyclic_lr


class LearningRateManager:
    def __init__(self, method_name, config):
        self._config = config
        self.method_name = method_name

        self.method_options = {
            'exponential': tf.train.exponential_decay,
            'cyclic': cyclic_learning_rate,
            'linear': tf.train.linear_cosine_decay,
            'test_lr': tf.train.linear_cosine_decay,
        }
        self.method_function = self.method_options[self.method_name]

    def get_learning_rate(self, global_step):
        return self.method_function(global_step=global_step, **self._config)
