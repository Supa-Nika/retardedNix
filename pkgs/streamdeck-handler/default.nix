{ pkgs }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    opencv4
    pyserial
    numpy
    pillow
    pyautogui
    yt-dlp
  ]);

  gstPluginPath = pkgs.lib.makeSearchPathOutput "lib" "lib/gstreamer-1.0" [
    pkgs.gst_all_1.gst-plugins-base
    pkgs.gst_all_1.gst-plugins-good
    pkgs.gst_all_1.gst-plugins-bad
    pkgs.gst_all_1.gst-plugins-ugly
  ];

in
pkgs.stdenv.mkDerivation {
  pname = "streamdeck-handler";
  version = "0.2.0";

  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = name: type: baseNameOf name != "__pycache__";
  };
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/share/streamdeck-handler
    cp -r . $out/share/streamdeck-handler/

    # 1. Daemon binary
    makeWrapper ${pythonEnv}/bin/python $out/bin/streamdeck-daemon \
      --add-flags "$out/share/streamdeck-handler/daemon/daemon.py" \
      --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.ffmpeg pkgs.ydotool pkgs.pulseaudio ]} \
      --prefix PYTHONPATH : "$out/share/streamdeck-handler/daemon:$out/share/streamdeck-handler" \
      --set GST_PLUGIN_SYSTEM_PATH_1_0 "${gstPluginPath}" \
      --set STREAMDECK_FONT "${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSans.ttf" \
      --set STREAMDECK_FONT_BOLD "${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSans-Bold.ttf"

    # 2. CLI binary
    makeWrapper ${pythonEnv}/bin/python $out/bin/streamdeck-cli \
      --add-flags "$out/share/streamdeck-handler/cli.py"

    # 3. Music debug view (what the overlay sees: API values, position, lyric line)
    makeWrapper ${pythonEnv}/bin/python $out/bin/streamdeck-music-debug \
      --add-flags "-m modules.music.debug" \
      --prefix PYTHONPATH : "$out/share/streamdeck-handler/daemon"
  '';
}