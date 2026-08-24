"""Where the per-user store lives: --data-dir over FRECKLES_DATA_DIR over XDG."""


def test_xdg_default_when_nothing_is_set(world, tmp_path):
    xdg = tmp_path / "xdg"

    result = world.invoke(
        "heal",
        "--yes",
        env={"FRECKLES_DATA_DIR": None, "XDG_DATA_HOME": str(xdg)},
    )

    assert result.exit_code == 0
    assert (xdg / "freckles" / "store.sqlite").exists()


def test_env_var_beats_xdg(world, tmp_path):
    result = world.invoke("heal", "--yes", env={"XDG_DATA_HOME": str(tmp_path / "xdg")})

    assert result.exit_code == 0
    assert (world.data_dir / "store.sqlite").exists()
    assert not (tmp_path / "xdg" / "freckles" / "store.sqlite").exists()


def test_data_dir_option_beats_env(world, tmp_path):
    option_dir = tmp_path / "opt-data"

    result = world.invoke("--data-dir", str(option_dir), "heal", "--yes")

    assert result.exit_code == 0
    assert (option_dir / "store.sqlite").exists()
    assert not (world.data_dir / "store.sqlite").exists()
