{ pkgs }:

pkgs.qemu.overrideAttrs (oldAttrs: rec {
  version = "11.1.1";

  src = pkgs.fetchurl {
    url = "https://download.qemu.org/qemu-${version}.tar.xz";
    hash = "sha256-B5/7/4pxEbvIkCIQfLq/O7/WFNX8nXzGdZkRlqyhJII=";
  };

  # 1. Block QEMU from attempting to fetch packages from PyPI
  configureFlags = (oldAttrs.configureFlags or [ ]) ++ [
    "--disable-download"
  ];

  # 2. Provide Python build tools so QEMU can install its bundled offline wheels
  nativeBuildInputs = (oldAttrs.nativeBuildInputs or [ ]) ++ (with pkgs.python3Packages; [
    pip
    setuptools
    wheel
  ]);
})