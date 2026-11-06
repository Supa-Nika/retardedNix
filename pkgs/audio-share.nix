{ lib
, stdenv
, fetchurl
, autoPatchelfHook
, pipewire
}:

stdenv.mkDerivation rec {
  pname = "audio-share";
  version = "0.3.4";

  src = fetchurl {
    url = "https://github.com/mkckr0/audio-share/releases/download/v${version}/audio-share-server-cmd-linux.tar.gz";
    hash = "sha256-3PJculwZ8L7YwS7Hw3RSHlx9mL5Q0M6YhiUWELtDUk8=";
  };

  sourceRoot = "audio-share-server-cmd";

  nativeBuildInputs = [ autoPatchelfHook ];

  # as-cmd links against libpipewire-0.3, libgcc_s, libm and libc
  buildInputs = [
    (pipewire.lib or pipewire)
    stdenv.cc.cc.lib
  ];

  installPhase = ''
    runHook preInstall
    install -Dm755 bin/as-cmd $out/bin/as-cmd
    install -Dm644 LICENSE $out/share/licenses/${pname}/LICENSE
    runHook postInstall
  '';

  meta = {
    description = "Share a Linux/Windows PC's audio to an Android phone over the network (server, command line)";
    homepage = "https://github.com/mkckr0/audio-share";
    license = lib.licenses.asl20;
    platforms = [ "x86_64-linux" ];
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    mainProgram = "as-cmd";
  };
}
