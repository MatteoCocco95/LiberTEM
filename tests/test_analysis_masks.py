import pytest
import numpy as np
import scipy.sparse as sp
from libertem.masks import to_dense, to_sparse
from utils import MemoryDataSet, _naive_mask_apply, _mk_random


def _run_mask_test_program(lt_ctx, dataset, mask, expected):
    analysis_default = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask]
    )
    analysis_sparse = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: to_sparse(mask)], use_sparse=True
    )
    analysis_dense = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: to_dense(mask)], use_sparse=False
    )
    results_default = lt_ctx.run(analysis_default)
    results_sparse = lt_ctx.run(analysis_sparse)
    results_dense = lt_ctx.run(analysis_dense)

    assert np.allclose(
        results_default.mask_0.raw_data,
        expected
    )
    assert np.allclose(
        results_sparse.mask_0.raw_data,
        expected
    )
    assert np.allclose(
        results_dense.mask_0.raw_data,
        expected
    )


@pytest.mark.slow
def test_weird_partition_shapes_1_slow(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(1, 1, 16, 16), partition_shape=(16, 16, 2, 2))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)

    p = next(dataset.get_partitions())
    t = next(p.get_tiles())
    assert tuple(t.tile_slice.shape) == (1, 1, 2, 2)


def test_weird_partition_shapes_1_fast(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(1, 8, 16, 16), partition_shape=(16, 16, 8, 8))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)

    p = next(dataset.get_partitions())
    t = next(p.get_tiles())
    assert tuple(t.tile_slice.shape) == (1, 8, 8, 8)


def test_normal_partition_shape(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(1, 1, 16, 16), partition_shape=(1, 8, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_single_frame_tiles(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(1, 1, 16, 16), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


@pytest.mark.slow
def test_subframe_tiles_slow(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(1, 1, 4, 4), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_subframe_tiles_fast(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(1, 8, 4, 4), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_4d_tilesize(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_multirow_tileshape(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 16, 16, 16), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_mask_uint(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask = _mk_random(size=(16, 16)).astype("uint16")
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_endian(lt_ctx):
    data = np.random.choice(a=0xFFFF, size=(16, 16, 16, 16)).astype(">u2")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_signed(lt_ctx):
    data = np.random.choice(a=0xFFFF, size=(16, 16, 16, 16)).astype("<i4")
    mask = _mk_random(size=(16, 16))
    expected = _naive_mask_apply([mask], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))

    _run_mask_test_program(lt_ctx, dataset, mask, expected)


def test_multi_masks(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = _mk_random(size=(16, 16))
    mask1 = sp.csr_matrix(_mk_random(size=(16, 16)))
    expected = _naive_mask_apply([mask0, mask1], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1]
    )
    results = lt_ctx.run(analysis)

    assert np.allclose(
        results.mask_0.raw_data,
        expected[0],
    )
    assert np.allclose(
        results.mask_1.raw_data,
        expected[1],
    )


def test_mask_job(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = _mk_random(size=(16, 16))
    mask1 = sp.csr_matrix(_mk_random(size=(16, 16)))
    expected = _naive_mask_apply([mask0, mask1], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    job = lt_ctx.create_mask_job(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1]
    )
    results = lt_ctx.run(job)

    assert np.allclose(
        results,
        expected,
    )


def test_all_sparse_analysis(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = sp.csr_matrix(_mk_random(size=(16, 16)))
    mask1 = sp.csr_matrix(_mk_random(size=(16, 16)))
    expected = _naive_mask_apply([mask0, mask1], data)

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1]
    )
    results = lt_ctx.run(analysis)

    assert np.allclose(
        results.mask_0.raw_data,
        expected[0],
    )
    assert np.allclose(
        results.mask_1.raw_data,
        expected[1],
    )


def test_uses_sparse_all_default(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = sp.csr_matrix(_mk_random(size=(16, 16)))
    mask1 = sp.csr_matrix(_mk_random(size=(16, 16)))

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    job = lt_ctx.create_mask_job(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1]
    )

    tiles = job.dataset.get_partitions()
    tile = next(tiles)

    assert sp.issparse(job.masks[tile])


def test_uses_sparse_mixed_default(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = sp.csr_matrix(_mk_random(size=(16, 16)))
    mask1 = _mk_random(size=(16, 16))

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    job = lt_ctx.create_mask_job(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1]
    )
    tiles = job.dataset.get_partitions()
    tile = next(tiles)

    assert not sp.issparse(job.masks[tile])


def test_uses_sparse_true(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = _mk_random(size=(16, 16))
    mask1 = _mk_random(size=(16, 16))

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    job = lt_ctx.create_mask_job(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1], use_sparse=True
    )

    tiles = job.dataset.get_partitions()
    tile = next(tiles)

    assert sp.issparse(job.masks[tile])


def test_uses_sparse_false(lt_ctx):
    data = _mk_random(size=(16, 16, 16, 16), dtype="<u2")
    mask0 = sp.csr_matrix(_mk_random(size=(16, 16)))
    mask1 = sp.csr_matrix(_mk_random(size=(16, 16)))

    dataset = MemoryDataSet(data=data, tileshape=(4, 4, 4, 4), partition_shape=(16, 16, 16, 16))
    job = lt_ctx.create_mask_job(
        dataset=dataset, factories=[lambda: mask0, lambda: mask1], use_sparse=False
    )
    tiles = job.dataset.get_partitions()
    tile = next(tiles)

    assert not sp.issparse(job.masks[tile])


def test_masks_timeseries_2d_frames(lt_ctx):
    data = _mk_random(size=(16 * 16, 16, 16), dtype="<u2")
    dataset = MemoryDataSet(
        data=data,
        effective_shape=(16 * 16, 16, 16),
        tileshape=(2, 16, 16),
        partition_shape=(8, 16, 16)
    )
    mask0 = _mk_random(size=(16, 16))
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0]
    )
    results = lt_ctx.run(analysis)
    assert results.mask_0.raw_data.shape == (256,)


def test_masks_spectrum_linescan(lt_ctx):
    data = _mk_random(size=(16 * 16, 16 * 16), dtype="<u2")
    dataset = MemoryDataSet(
        data=data,
        effective_shape=(16 * 16, 16 * 16),
        tileshape=(2, 16 * 16),
        partition_shape=(8, 16 * 16),
        sig_dims=1,
    )
    mask0 = _mk_random(size=(16 * 16, ))
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0]
    )
    results = lt_ctx.run(analysis)
    assert results.mask_0.raw_data.shape == (16 * 16,)


def test_masks_spectrum(lt_ctx):
    data = _mk_random(size=(16, 16, 16 * 16), dtype="<u2")
    dataset = MemoryDataSet(
        data=data,
        effective_shape=(16, 16, 16 * 16),
        tileshape=(1, 2, 16 * 16),
        partition_shape=(1, 8, 16 * 16),
        sig_dims=1,
    )
    mask0 = _mk_random(size=(16 * 16, ))
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0]
    )
    results = lt_ctx.run(analysis)
    assert results.mask_0.raw_data.shape == (16, 16)


def test_masks_hyperspectral(lt_ctx):
    # flat navigation dimension to simulate "image stack"-like file formats:
    data = _mk_random(size=(16 * 16, 16, 16, 16), dtype="<u2")
    dataset = MemoryDataSet(
        data=data,
        effective_shape=(16, 16, 16, 16, 16),
        tileshape=(1, 16, 16, 16),
        partition_shape=(8, 16, 16, 16),
        sig_dims=3,
    )
    mask0 = _mk_random(size=(16, 16, 16))
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0]
    )
    results = lt_ctx.run(analysis)
    assert results.mask_0.raw_data.shape == (16, 16)


def test_masks_complex_ds(lt_ctx, ds_complex):
    mask0 = _mk_random(size=(16, 16))
    analysis = lt_ctx.create_mask_analysis(
        dataset=ds_complex, factories=[lambda: mask0]
    )
    results = lt_ctx.run(analysis)
    assert results.mask_0.raw_data.shape == (16, 16)


def test_masks_complex_mask(lt_ctx, ds_complex):
    mask0 = _mk_random(size=(16, 16), dtype="complex64")
    analysis = lt_ctx.create_mask_analysis(
        dataset=ds_complex, factories=[lambda: mask0]
    )
    expected = _naive_mask_apply([mask0], ds_complex.data)
    results = lt_ctx.run(analysis)
    assert results.mask_0_complex.raw_data.shape == (16, 16)
    assert np.allclose(
        results.mask_0_complex.raw_data,
        expected
    )

    # also execute _run_mask_test_program to check sparse implementation.
    # _run_mask_test_program checks mask_0 result, which is np.abs(mask_0_complex)
    _run_mask_test_program(lt_ctx, ds_complex, mask0, np.abs(expected))


def test_numerics(lt_ctx):
    dtype = 'float32'
    # Highest expected detector resolution
    RESOLUTION = 4096
    # Highest expected detector dynamic range
    RANGE = 1e6
    # default value for all cells
    # The test fails for 1.1 using float32!
    VAL = 1.0

    data = np.full((2, 2, RESOLUTION, RESOLUTION), VAL, dtype=dtype)
    data[0, 0, 0, 0] += VAL * RANGE
    dataset = MemoryDataSet(
        data=data,
        effective_shape=(2, 2, RESOLUTION, RESOLUTION),
        tileshape=(1, 2, RESOLUTION, RESOLUTION),
        partition_shape=(1, 2, RESOLUTION, RESOLUTION),
        sig_dims=2,
    )
    mask0 = np.ones((RESOLUTION, RESOLUTION), dtype=dtype)
    analysis = lt_ctx.create_mask_analysis(
        dataset=dataset, factories=[lambda: mask0]
    )

    results = lt_ctx.run(analysis)
    expected = np.array([[
        [VAL*RESOLUTION**2 + VAL*RANGE, VAL*RESOLUTION**2],
        [VAL*RESOLUTION**2, VAL*RESOLUTION**2]
    ]])
    naive = _naive_mask_apply([mask0], data)

    # print(expected)
    # print(naive)
    # print(results.mask_0.raw_data)

    assert np.allclose(expected, naive)
    assert np.allclose(expected[0], results.mask_0.raw_data)
