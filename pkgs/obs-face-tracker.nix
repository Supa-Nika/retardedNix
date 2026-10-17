# nix/pkgs/obs-face-tracker.nix
{ pkgs }:

pkgs.stdenv.mkDerivation rec {
  pname = "obs-face-tracker";
  version = "0.9.1";

  src = pkgs.fetchFromGitHub {
    owner = "norihiro";
    repo = "obs-face-tracker";
    rev = version;
    hash = "sha256-mlbzuXcXyw3DVPKl0sZZfLNXj9plF4pYQg+DGzKqTxw=";
    fetchSubmodules = true;
  };

  nativeBuildInputs = [ 
    pkgs.cmake
    pkgs.pkg-config
    pkgs.qt6.wrapQtAppsHook
  ];

  buildInputs = [
    pkgs.obs-studio
    pkgs.dlib
    pkgs.openblas
    pkgs.opencv
    pkgs.qt6.qtbase
    pkgs.qt6.qt5compat
  ];

  preConfigure = ''
    substituteInPlace CMakeLists.txt \
      --replace-fail 'Core Gui' 'Core Gui GuiPrivate'
  '';

  cmakeFlags = [
    "-DCMAKE_INSTALL_PREFIX=${placeholder "out"}"
    "-DQT_VERSION=6"
  ];

  postInstall = ''
    mkdir -p $out/lib/obs-plugins
    if [ -d "$out/obs-plugins/64bit" ]; then
      mv $out/obs-plugins/64bit/*.so $out/lib/obs-plugins/
      rm -rf $out/obs-plugins
    elif [ -f "$out/bin/64bit/obs-face-tracker.so" ]; then
      mv $out/bin/64bit/*.so $out/lib/obs-plugins/
    fi

    mkdir -p $out/share/obs/obs-plugins/obs-face-tracker
    if [ -d "$out/data/obs-plugins/obs-face-tracker" ]; then
      cp -r $out/data/obs-plugins/obs-face-tracker/* $out/share/obs/obs-plugins/obs-face-tracker/
      rm -rf $out/data
    elif [ -d "$out/share/obs/obs-plugins/obs-face-tracker/obs-plugins/obs-face-tracker" ]; then
      cp -r $out/share/obs/obs-plugins/obs-face-tracker/obs-plugins/obs-face-tracker/* $out/share/obs/obs-plugins/obs-face-tracker/
      rm -rf $out/share/obs/obs-plugins/obs-face-tracker/obs-plugins
    fi
  '';
}