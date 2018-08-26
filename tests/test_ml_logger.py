"""
# Tests for ml-logger.

## Testing with a server

To test with a live server, first run (in a separate console)
```
python -m ml_logger.server --log-dir /tmp/ml-logger-debug
```
or do:
```bash
make start-test-server
```

Then run this test script with the option:
```bash
python -m pytest tests --capture=no --log-dir http://0.0.0.0:8081
```
or do
```bash
make test-with-server
```
"""
import pytest
from time import sleep
from os.path import join as pathJoin
from ml_logger import logger, Color, percent


@pytest.fixture(scope='session')
def log_dir(request):
    return request.config.getoption('--log-dir')


@pytest.fixture(scope="session")
def setup(log_dir):
    logger.configure(log_dir, prefix='main_test_script')
    logger.remove('')
    logger.log_line('hey')
    sleep(1.0)

    print(f"logging to {pathJoin(logger.log_directory, logger.prefix)}")

def test_configuration(log_dir):
    logger.configure(log_dir, prefix='main_test_script', color='green')
    logger.log("This is a unittest")
    logger.log("Some stats", reward=0.05, kl=0.001)
    logger.flush()


def test_load_pkl_log(setup):
    import numpy
    d1 = numpy.random.randn(20, 10)
    logger.log_pkl(d1, 'test_file.pkl')
    sleep(1.0)
    d2 = numpy.random.randn(20, 10)
    logger.log_pkl(d2, 'test_file.pkl')
    sleep(1.0)

    data = logger.load_pkl_log('test_file.pkl')
    assert len(data) == 2, "data should contain two arrays"
    assert numpy.array_equal(data[0], d1), "first should be the same as d1"
    assert numpy.array_equal(data[1], d2), "first should be the same as d2"


def test_log_data(setup):
    import numpy
    d1 = numpy.random.randn(20, 10)
    logger.log_pkl(d1, 'test_file.pkl')
    sleep(1.0)
    d2 = numpy.random.randn(20, 10)
    logger.dump_pkl(d2, 'test_file.pkl')
    sleep(1.0)

    data = logger.load_pkl_log('test_file.pkl')
    assert len(data) == 1, "data should contain only one array because we overwrote it."
    assert numpy.array_equal(data[0], d2), "first should be the same as d2"


def test(setup):
    d = Color(3.1415926, 'red')
    s = "{:.1}".format(d)
    print(s)

    logger.log_params(G=dict(some_config="hey"))
    logger.log(step=0, some=Color(0.1, 'yellow'))
    logger.log(step=1, some=Color(0.28571, 'yellow', lambda v: "{:.5f}%".format(v * 100)))
    logger.log(step=2, some=Color(0.85, 'yellow', percent))
    logger.log({"some_var/smooth": 10}, some=Color(0.85, 'yellow', percent), step=3)
    logger.log(step=4, some=Color(10, 'yellow'))


def test_image(setup):
    import scipy.misc
    import numpy as np

    image_bw = np.zeros((64, 64, 1), dtype=np.uint8)
    image_bw_2 = scipy.misc.face(gray=True)[::4, ::4]
    image_rgb = np.zeros((64, 64, 3), dtype=np.uint8)
    image_rgba = scipy.misc.face()[::4, ::4, :]
    logger.log_image(image_bw, "black_white.png")
    logger.log_image(image_bw_2, "bw_face.png")
    logger.log_image(image_rgb, 'rgb.png')
    logger.log_image(image_rgba, f'rgba_face_{100}.png')
    logger.log_image(image_bw, f"bw_{100}.png")
    logger.log_image(image_rgba, f"rbga_{100}.png")

    # todo: animation is NOT implemented.
    # now print a stack
    # for i in range(10):
    #     logger.log_image(i, animation=[image_rgba] * 5)


def test_pyplot(setup):
    import scipy.misc
    import matplotlib
    matplotlib.use('TKAgg')
    import matplotlib.pyplot as plt
    import numpy as np

    face = scipy.misc.face()
    logger.log_image(face, "face.png")

    fig = plt.figure(figsize=(4, 2))
    xs = np.linspace(0, 5, 1000)
    plt.plot(xs, np.cos(xs))
    logger.savefig("face_02.png", fig=fig)
    plt.close()

    fig = plt.figure(figsize=(4, 2))
    xs = np.linspace(0, 5, 1000)
    plt.plot(xs, np.cos(xs))
    logger.savefig('sine.pdf')


def test_video(setup):
    import numpy as np

    def im(x, y):
        canvas = np.zeros((200, 200))
        for i in range(200):
            for j in range(200):
                if x - 5 < i < x + 5 and y - 5 < j < y + 5:
                    canvas[i, j] = 1
        return canvas

    frames = [im(100 + i, 80) for i in range(20)]

    logger.log_video(frames, "test_video.mp4")


class FakeTensor:
    def cpu(self):
        return self

    def detach(self):
        return self

    def numpy(self):
        import numpy as np
        return np.ones([100, 2])


class FakeModule:
    @staticmethod
    def state_dict():
        return dict(var_1=FakeTensor())


@pytest.fixture
def test_module(setup):
    logger.log_module(Test=FakeModule, step=0, )
    sleep(1.0)


def test_load_module(setup, test_module):
    result, = logger.load_pkl_log(f"modules/{0:04d}_Test.pkl")
    import numpy as np
    assert (result['var_1'] == np.ones([100, 2])).all(), "should be the same as test data"


def test_load_params(setup):
    pass


def test_diff(setup):
    logger.diff()


def test_git_rev(setup):
    print([logger.__head__])


def test_current_branch(setup):
    print([logger.__current_branch__])


def test_hostname(setup):
    assert len(logger.hostname) > 0, 'hostname should be non-trivial'
    print([logger.hostname])


def test_split(setup):
    assert logger.split() is None, 'The first tick should be None'
    assert type(logger.split()) is float, 'Then it should return a a float in the seconds.'


def test_ping(setup):
    print('test ping starts')
    signals = logger.ping('alive', 0.1)
    print(f"signals => {signals}")
    sleep(0.2)
    signals = logger.ping('alive', 0.2)
    print(f"signals => {signals}")

    logger.logger.send_signal(logger.prefix, signal="stop")
    sleep(0.25)
    logger.logger.send_signal(logger.prefix, signal="pause")
    sleep(0.15)

    for i in range(4):
        signals = logger.ping('other ping')
        print(f"signals => {signals}")
        sleep(0.4)

    logger.ping('completed')
