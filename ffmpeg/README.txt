FFmpeg 64-bit static Windows build from www.gyan.dev

Version: 2025-06-16-git-e6fb8f373e-full_build-www.gyan.dev

License: GPL v3

Source Code: https://github.com/FFmpeg/FFmpeg/commit/e6fb8f373e

External Assets
frei0r plugins:   https://www.gyan.dev/ffmpeg/builds/ffmpeg-frei0r-plugins
lensfun database: https://www.gyan.dev/ffmpeg/builds/ffmpeg-lensfun-db

git-full build configuration: 

ARCH                      x86 (generic)
big-endian                no
runtime cpu detection     yes
standalone assembly       yes
x86 assembler             nasm
MMX enabled               yes
MMXEXT enabled            yes
3DNow! enabled            yes
3DNow! extended enabled   yes
SSE enabled               yes
SSSE3 enabled             yes
AESNI enabled             yes
AVX enabled               yes
AVX2 enabled              yes
AVX-512 enabled           yes
AVX-512ICL enabled        yes
XOP enabled               yes
FMA3 enabled              yes
FMA4 enabled              yes
i686 features enabled     yes
CMOV is fast              yes
EBX available             yes
EBP available             yes
debug symbols             yes
strip symbols             yes
optimize for size         no
optimizations             yes
static                    yes
shared                    no
network support           yes
threading support         pthreads
safe bitstream reader     yes
texi2html enabled         no
perl enabled              yes
pod2man enabled           yes
makeinfo enabled          yes
makeinfo supports HTML    yes
xmllint enabled           yes

External libraries:
avisynth                libgsm                  libssh
bzlib                   libharfbuzz             libsvtav1
chromaprint             libilbc                 libtheora
frei0r                  libjxl                  libtwolame
gmp                     liblc3                  libuavs3d
gnutls                  liblensfun              libvidstab
iconv                   libmodplug              libvmaf
ladspa                  libmp3lame              libvo_amrwbenc
lcms2                   libmysofa               libvorbis
libaom                  liboapv                 libvpx
libaribb24              libopencore_amrnb       libvvenc
libaribcaption          libopencore_amrwb       libwebp
libass                  libopenjpeg             libx264
libbluray               libopenmpt              libx265
libbs2b                 libopus                 libxavs2
libcaca                 libplacebo              libxevd
libcdio                 libqrencode             libxeve
libcodec2               libquirc                libxml2
libdav1d                librav1e                libxvid
libdavs2                librist                 libzimg
libdvdnav               librubberband           libzmq
libdvdread              libshaderc              libzvbi
libflite                libshine                lzma
libfontconfig           libsnappy               mediafoundation
libfreetype             libsoxr                 openal
libfribidi              libspeex                sdl2
libgme                  libsrt                  zlib

External libraries providing hardware acceleration:
amf                     d3d12va                 nvdec
cuda                    dxva2                   nvenc
cuda_llvm               ffnvcodec               opencl
cuvid                   libmfx                  vaapi
d3d11va                 libvpl                  vulkan

Libraries:
avcodec                 avformat                swscale
avdevice                avutil
avfilter                swresample

Programs:
ffmpeg                  ffplay                  ffprobe

Enabled decoders:
aac                     g2m                     pcm_u8
aac_fixed               g723_1                  pcm_vidc
aac_latm                g729                    pcx
aasc                    gdv                     pdv
ac3                     gem                     pfm
ac3_fixed               gif                     pgm
acelp_kelvin            gremlin_dpcm            pgmyuv
adpcm_4xm               gsm                     pgssub
adpcm_adx               gsm_ms                  pgx
adpcm_afc               h261                    phm
adpcm_agm               h263                    photocd
adpcm_aica              h263i                   pictor
adpcm_argo              h263p                   pixlet
adpcm_ct                h264                    pjs
adpcm_dtk               h264_amf                png
adpcm_ea                h264_cuvid              ppm
adpcm_ea_maxis_xa       h264_qsv                prores
adpcm_ea_r1             hap                     prosumer
adpcm_ea_r2             hca                     psd
adpcm_ea_r3             hcom                    ptx
adpcm_ea_xas            hdr                     qcelp
adpcm_g722              hevc                    qdm2
adpcm_g726              hevc_amf                qdmc
adpcm_g726le            hevc_cuvid              qdraw
adpcm_ima_acorn         hevc_qsv                qoa
adpcm_ima_alp           hnm4_video              qoi
adpcm_ima_amv           hq_hqa                  qpeg
adpcm_ima_apc           hqx                     qtrle
adpcm_ima_apm           huffyuv                 r10k
adpcm_ima_cunning       hymt                    r210
adpcm_ima_dat4          iac                     ra_144
adpcm_ima_dk3           idcin                   ra_288
adpcm_ima_dk4           idf                     ralf
adpcm_ima_ea_eacs       iff_ilbm                rasc
adpcm_ima_ea_sead       ilbc                    rawvideo
adpcm_ima_iss           imc                     realtext
adpcm_ima_moflex        imm4                    rka
adpcm_ima_mtf           imm5                    rl2
adpcm_ima_oki           indeo2                  roq
adpcm_ima_qt            indeo3                  roq_dpcm
adpcm_ima_rad           indeo4                  rpza
adpcm_ima_smjpeg        indeo5                  rscc
adpcm_ima_ssi           interplay_acm           rtv1
adpcm_ima_wav           interplay_dpcm          rv10
adpcm_ima_ws            interplay_video         rv20
adpcm_ima_xbox          ipu                     rv30
adpcm_ms                jacosub                 rv40
adpcm_mtaf              jpeg2000                rv60
adpcm_psx               jpegls                  s302m
adpcm_sbpro_2           jv                      sami
adpcm_sbpro_3           kgv1                    sanm
adpcm_sbpro_4           kmvc                    sbc
adpcm_swf               lagarith                scpr
adpcm_thp               lead                    screenpresso
adpcm_thp_le            libaom_av1              sdx2_dpcm
adpcm_vima              libaribb24              sga
adpcm_xa                libaribcaption          sgi
adpcm_xmd               libcodec2               sgirle
adpcm_yamaha            libdav1d                sheervideo
adpcm_zork              libdavs2                shorten
agm                     libgsm                  simbiosis_imx
aic                     libgsm_ms               sipr
alac                    libilbc                 siren
alias_pix               libjxl                  smackaud
als                     libjxl_anim             smacker
amrnb                   liblc3                  smc
amrwb                   libopencore_amrnb       smvjpeg
amv                     libopencore_amrwb       snow
anm                     libopus                 sol_dpcm
ansi                    libspeex                sonic
anull                   libuavs3d               sp5x
apac                    libvorbis               speedhq
ape                     libvpx_vp8              speex
apng                    libvpx_vp9              srgc
aptx                    libxevd                 srt
aptx_hd                 libzvbi_teletext        ssa
apv                     loco                    stl
arbc                    lscr                    subrip
argo                    m101                    subviewer
ass                     mace3                   subviewer1
asv1                    mace6                   sunrast
asv2                    magicyuv                svq1
atrac1                  mdec                    svq3
atrac3                  media100                tak
atrac3al                metasound               targa
atrac3p                 microdvd                targa_y216
atrac3pal               mimic                   tdsc
atrac9                  misc4                   text
aura                    mjpeg                   theora
aura2                   mjpeg_cuvid             thp
av1                     mjpeg_qsv               tiertexseqvideo
av1_amf                 mjpegb                  tiff
av1_cuvid               mlp                     tmv
av1_qsv                 mmvideo                 truehd
avrn                    mobiclip                truemotion1
avrp                    motionpixels            truemotion2
avs                     movtext                 truemotion2rt
avui                    mp1                     truespeech
bethsoftvid             mp1float                tscc
bfi                     mp2                     tscc2
bink                    mp2float                tta
binkaudio_dct           mp3                     twinvq
binkaudio_rdft          mp3adu                  txd
bintext                 mp3adufloat             ulti
bitpacked               mp3float                utvideo
bmp                     mp3on4                  v210
bmv_audio               mp3on4float             v210x
bmv_video               mpc7                    v308
bonk                    mpc8                    v408
brender_pix             mpeg1_cuvid             v410
c93                     mpeg1video              vb
cavs                    mpeg2_cuvid             vble
cbd2_dpcm               mpeg2_qsv               vbn
ccaption                mpeg2video              vc1
cdgraphics              mpeg4                   vc1_cuvid
cdtoons                 mpeg4_cuvid             vc1_qsv
cdxl                    mpegvideo               vc1image
cfhd                    mpl2                    vcr1
cinepak                 msa1                    vmdaudio
clearvideo              mscc                    vmdvideo
cljr                    msmpeg4v1               vmix
cllc                    msmpeg4v2               vmnc
comfortnoise            msmpeg4v3               vnull
cook                    msnsiren                vorbis
cpia                    msp2                    vp3
cri                     msrle                   vp4
cscd                    mss1                    vp5
cyuv                    mss2                    vp6
dca                     msvideo1                vp6a
dds                     mszh                    vp6f
derf_dpcm               mts2                    vp7
dfa                     mv30                    vp8
dfpwm                   mvc1                    vp8_cuvid
dirac                   mvc2                    vp8_qsv
dnxhd                   mvdv                    vp9
dolby_e                 mvha                    vp9_cuvid
dpx                     mwsc                    vp9_qsv
dsd_lsbf                mxpeg                   vplayer
dsd_lsbf_planar         nellymoser              vqa
dsd_msbf                notchlc                 vqc
dsd_msbf_planar         nuv                     vvc
dsicinaudio             on2avc                  vvc_qsv
dsicinvideo             opus                    wady_dpcm
dss_sp                  osq                     wavarc
dst                     paf_audio               wavpack
dvaudio                 paf_video               wbmp
dvbsub                  pam                     wcmv
dvdsub                  pbm                     webp
dvvideo                 pcm_alaw                webvtt
dxa                     pcm_bluray              wmalossless
dxtory                  pcm_dvd                 wmapro
dxv                     pcm_f16le               wmav1
eac3                    pcm_f24le               wmav2
eacmv                   pcm_f32be               wmavoice
eamad                   pcm_f32le               wmv1
eatgq                   pcm_f64be               wmv2
eatgv                   pcm_f64le               wmv3
eatqi                   pcm_lxf                 wmv3image
eightbps                pcm_mulaw               wnv1
eightsvx_exp            pcm_s16be               wrapped_avframe
eightsvx_fib            pcm_s16be_planar        ws_snd1
escape124               pcm_s16le               xan_dpcm
escape130               pcm_s16le_planar        xan_wc3
evrc                    pcm_s24be               xan_wc4
exr                     pcm_s24daud             xbin
fastaudio               pcm_s24le               xbm
ffv1                    pcm_s24le_planar        xface
ffvhuff                 pcm_s32be               xl
ffwavesynth             pcm_s32le               xma1
fic                     pcm_s32le_planar        xma2
fits                    pcm_s64be               xpm
flac                    pcm_s64le               xsub
flashsv                 pcm_s8                  xwd
flashsv2                pcm_s8_planar           y41p
flic                    pcm_sga                 ylc
flv                     pcm_u16be               yop
fmvc                    pcm_u16le               yuv4
fourxm                  pcm_u24be               zero12v
fraps                   pcm_u24le               zerocodec
frwu                    pcm_u32be               zlib
ftr                     pcm_u32le               zmbv

Enabled encoders:
a64multi                hevc_qsv                pcm_s64be
a64multi5               hevc_vaapi              pcm_s64le
aac                     hevc_vulkan             pcm_s8
aac_mf                  huffyuv                 pcm_s8_planar
ac3                     jpeg2000                pcm_u16be
ac3_fixed               jpegls                  pcm_u16le
ac3_mf                  libaom_av1              pcm_u24be
adpcm_adx               libcodec2               pcm_u24le
adpcm_argo              libgsm                  pcm_u32be
adpcm_g722              libgsm_ms               pcm_u32le
adpcm_g726              libilbc                 pcm_u8
adpcm_g726le            libjxl                  pcm_vidc
adpcm_ima_alp           libjxl_anim             pcx
adpcm_ima_amv           liblc3                  pfm
adpcm_ima_apm           libmp3lame              pgm
adpcm_ima_qt            liboapv                 pgmyuv
adpcm_ima_ssi           libopencore_amrnb       phm
adpcm_ima_wav           libopenjpeg             png
adpcm_ima_ws            libopus                 ppm
adpcm_ms                librav1e                prores
adpcm_swf               libshine                prores_aw
adpcm_yamaha            libspeex                prores_ks
alac                    libsvtav1               qoi
alias_pix               libtheora               qtrle
amv                     libtwolame              r10k
anull                   libvo_amrwbenc          r210
apng                    libvorbis               ra_144
aptx                    libvpx_vp8              rawvideo
aptx_hd                 libvpx_vp9              roq
ass                     libvvenc                roq_dpcm
asv1                    libwebp                 rpza
asv2                    libwebp_anim            rv10
av1_amf                 libx264                 rv20
av1_mf                  libx264rgb              s302m
av1_nvenc               libx265                 sbc
av1_qsv                 libxavs2                sgi
av1_vaapi               libxeve                 smc
avrp                    libxvid                 snow
avui                    ljpeg                   speedhq
bitpacked               magicyuv                srt
bmp                     mjpeg                   ssa
cfhd                    mjpeg_qsv               subrip
cinepak                 mjpeg_vaapi             sunrast
cljr                    mlp                     svq1
comfortnoise            movtext                 targa
dca                     mp2                     text
dfpwm                   mp2fixed                tiff
dnxhd                   mp3_mf                  truehd
dpx                     mpeg1video              tta
dvbsub                  mpeg2_qsv               ttml
dvdsub                  mpeg2_vaapi             utvideo
dvvideo                 mpeg2video              v210
dxv                     mpeg4                   v308
eac3                    msmpeg4v2               v408
exr                     msmpeg4v3               v410
ffv1                    msrle                   vbn
ffv1_vulkan             msvideo1                vc2
ffvhuff                 nellymoser              vnull
fits                    opus                    vorbis
flac                    pam                     vp8_vaapi
flashsv                 pbm                     vp9_qsv
flashsv2                pcm_alaw                vp9_vaapi
flv                     pcm_bluray              wavpack
g723_1                  pcm_dvd                 wbmp
gif                     pcm_f32be               webvtt
h261                    pcm_f32le               wmav1
h263                    pcm_f64be               wmav2
h263p                   pcm_f64le               wmv1
h264_amf                pcm_mulaw               wmv2
h264_mf                 pcm_s16be               wrapped_avframe
h264_nvenc              pcm_s16be_planar        xbm
h264_qsv                pcm_s16le               xface
h264_vaapi              pcm_s16le_planar        xsub
h264_vulkan             pcm_s24be               xwd
hap                     pcm_s24daud             y41p
hdr                     pcm_s24le               yuv4
hevc_amf                pcm_s24le_planar        zlib
hevc_d3d12va            pcm_s32be               zmbv
hevc_mf                 pcm_s32le
hevc_nvenc              pcm_s32le_planar

Enabled hwaccels:
av1_d3d11va             hevc_dxva2              vc1_nvdec
av1_d3d11va2            hevc_nvdec              vc1_vaapi
av1_d3d12va             hevc_vaapi              vp8_nvdec
av1_dxva2               hevc_vulkan             vp8_vaapi
av1_nvdec               mjpeg_nvdec             vp9_d3d11va
av1_vaapi               mjpeg_vaapi             vp9_d3d11va2
av1_vulkan              mpeg1_nvdec             vp9_d3d12va
ffv1_vulkan             mpeg2_d3d11va           vp9_dxva2
h263_vaapi              mpeg2_d3d11va2          vp9_nvdec
h264_d3d11va            mpeg2_d3d12va           vp9_vaapi
h264_d3d11va2           mpeg2_dxva2             vvc_vaapi
h264_d3d12va            mpeg2_nvdec             wmv3_d3d11va
h264_dxva2              mpeg2_vaapi             wmv3_d3d11va2
h264_nvdec              mpeg4_nvdec             wmv3_d3d12va
h264_vaapi              mpeg4_vaapi             wmv3_dxva2
h264_vulkan             vc1_d3d11va             wmv3_nvdec
hevc_d3d11va            vc1_d3d11va2            wmv3_vaapi
hevc_d3d11va2           vc1_d3d12va
hevc_d3d12va            vc1_dxva2

Enabled parsers:
aac                     dvd_nav                 mpeg4video
aac_latm                dvdsub                  mpegaudio
ac3                     evc                     mpegvideo
adx                     ffv1                    opus
amr                     flac                    png
apv                     ftr                     pnm
av1                     g723_1                  qoi
avs2                    g729                    rv34
avs3                    gif                     sbc
bmp                     gsm                     sipr
cavsvideo               h261                    tak
cook                    h263                    vc1
cri                     h264                    vorbis
dca                     hdr                     vp3
dirac                   hevc                    vp8
dnxhd                   ipu                     vp9
dnxuc                   jpeg2000                vvc
dolby_e                 jpegxl                  webp
dpx                     misc4                   xbm
dvaudio                 mjpeg                   xma
dvbsub                  mlp                     xwd

Enabled demuxers:
aa                      idcin                   pcm_f64le
aac                     idf                     pcm_mulaw
aax                     iff                     pcm_s16be
ac3                     ifv                     pcm_s16le
ac4                     ilbc                    pcm_s24be
ace                     image2                  pcm_s24le
acm                     image2_alias_pix        pcm_s32be
act                     image2_brender_pix      pcm_s32le
adf                     image2pipe              pcm_s8
adp                     image_bmp_pipe          pcm_u16be
ads                     image_cri_pipe          pcm_u16le
adx                     image_dds_pipe          pcm_u24be
aea                     image_dpx_pipe          pcm_u24le
afc                     image_exr_pipe          pcm_u32be
aiff                    image_gem_pipe          pcm_u32le
aix                     image_gif_pipe          pcm_u8
alp                     image_hdr_pipe          pcm_vidc
amr                     image_j2k_pipe          pdv
amrnb                   image_jpeg_pipe         pjs
amrwb                   image_jpegls_pipe       pmp
anm                     image_jpegxl_pipe       pp_bnk
apac                    image_pam_pipe          pva
apc                     image_pbm_pipe          pvf
ape                     image_pcx_pipe          qcp
apm                     image_pfm_pipe          qoa
apng                    image_pgm_pipe          r3d
aptx                    image_pgmyuv_pipe       rawvideo
aptx_hd                 image_pgx_pipe          rcwt
apv                     image_phm_pipe          realtext
aqtitle                 image_photocd_pipe      redspark
argo_asf                image_pictor_pipe       rka
argo_brp                image_png_pipe          rl2
argo_cvg                image_ppm_pipe          rm
asf                     image_psd_pipe          roq
asf_o                   image_qdraw_pipe        rpl
ass                     image_qoi_pipe          rsd
ast                     image_sgi_pipe          rso
au                      image_sunrast_pipe      rtp
av1                     image_svg_pipe          rtsp
avi                     image_tiff_pipe         s337m
avisynth                image_vbn_pipe          sami
avr                     image_webp_pipe         sap
avs                     image_xbm_pipe          sbc
avs2                    image_xpm_pipe          sbg
avs3                    image_xwd_pipe          scc
bethsoftvid             imf                     scd
bfi                     ingenient               sdns
bfstm                   ipmovie                 sdp
bink                    ipu                     sdr2
binka                   ircam                   sds
bintext                 iss                     sdx
bit                     iv8                     segafilm
bitpacked               ivf                     ser
bmv                     ivr                     sga
boa                     jacosub                 shorten
bonk                    jpegxl_anim             siff
brstm                   jv                      simbiosis_imx
c93                     kux                     sln
caf                     kvag                    smacker
cavsvideo               laf                     smjpeg
cdg                     lc3                     smush
cdxl                    libgme                  sol
cine                    libmodplug              sox
codec2                  libopenmpt              spdif
codec2raw               live_flv                srt
concat                  lmlm4                   stl
dash                    loas                    str
data                    lrc                     subviewer
daud                    luodat                  subviewer1
dcstr                   lvf                     sup
derf                    lxf                     svag
dfa                     m4v                     svs
dfpwm                   matroska                swf
dhav                    mca                     tak
dirac                   mcc                     tedcaptions
dnxhd                   mgsts                   thp
dsf                     microdvd                threedostr
dsicin                  mjpeg                   tiertexseq
dss                     mjpeg_2000              tmv
dts                     mlp                     truehd
dtshd                   mlv                     tta
dv                      mm                      tty
dvbsub                  mmf                     txd
dvbtxt                  mods                    ty
dvdvideo                moflex                  usm
dxa                     mov                     v210
ea                      mp3                     v210x
ea_cdata                mpc                     vag
eac3                    mpc8                    vc1
epaf                    mpegps                  vc1t
evc                     mpegts                  vividas
ffmetadata              mpegtsraw               vivo
filmstrip               mpegvideo               vmd
fits                    mpjpeg                  vobsub
flac                    mpl2                    voc
flic                    mpsub                   vpk
flv                     msf                     vplayer
fourxm                  msnwc_tcp               vqf
frm                     msp                     vvc
fsb                     mtaf                    w64
fwse                    mtv                     wady
g722                    musx                    wav
g723_1                  mv                      wavarc
g726                    mvi                     wc3
g726le                  mxf                     webm_dash_manifest
g729                    mxg                     webvtt
gdv                     nc                      wsaud
genh                    nistsphere              wsd
gif                     nsp                     wsvqa
gsm                     nsv                     wtv
gxf                     nut                     wv
h261                    nuv                     wve
h263                    obu                     xa
h264                    ogg                     xbin
hca                     oma                     xmd
hcom                    osq                     xmv
hevc                    paf                     xvag
hls                     pcm_alaw                xwma
hnm                     pcm_f32be               yop
iamf                    pcm_f32le               yuv4mpegpipe
ico                     pcm_f64be

Enabled muxers:
a64                     h261                    pcm_s16le
ac3                     h263                    pcm_s24be
ac4                     h264                    pcm_s24le
adts                    hash                    pcm_s32be
adx                     hds                     pcm_s32le
aea                     hevc                    pcm_s8
aiff                    hls                     pcm_u16be
alp                     iamf                    pcm_u16le
amr                     ico                     pcm_u24be
amv                     ilbc                    pcm_u24le
apm                     image2                  pcm_u32be
apng                    image2pipe              pcm_u32le
aptx                    ipod                    pcm_u8
aptx_hd                 ircam                   pcm_vidc
apv                     ismv                    psp
argo_asf                ivf                     rawvideo
argo_cvg                jacosub                 rcwt
asf                     kvag                    rm
asf_stream              latm                    roq
ass                     lc3                     rso
ast                     lrc                     rtp
au                      m4v                     rtp_mpegts
avi                     matroska                rtsp
avif                    matroska_audio          sap
avm2                    md5                     sbc
avs2                    microdvd                scc
avs3                    mjpeg                   segafilm
bit                     mkvtimestamp_v2         segment
caf                     mlp                     smjpeg
cavsvideo               mmf                     smoothstreaming
chromaprint             mov                     sox
codec2                  mp2                     spdif
codec2raw               mp3                     spx
crc                     mp4                     srt
dash                    mpeg1system             stream_segment
data                    mpeg1vcd                streamhash
daud                    mpeg1video              sup
dfpwm                   mpeg2dvd                swf
dirac                   mpeg2svcd               tee
dnxhd                   mpeg2video              tg2
dts                     mpeg2vob                tgp
dv                      mpegts                  truehd
eac3                    mpjpeg                  tta
evc                     mxf                     ttml
f4v                     mxf_d10                 uncodedframecrc
ffmetadata              mxf_opatom              vc1
fifo                    null                    vc1t
filmstrip               nut                     voc
fits                    obu                     vvc
flac                    oga                     w64
flv                     ogg                     wav
framecrc                ogv                     webm
framehash               oma                     webm_chunk
framemd5                opus                    webm_dash_manifest
g722                    pcm_alaw                webp
g723_1                  pcm_f32be               webvtt
g726                    pcm_f32le               wsaud
g726le                  pcm_f64be               wtv
gif                     pcm_f64le               wv
gsm                     pcm_mulaw               yuv4mpegpipe
gxf                     pcm_s16be

Enabled protocols:
async                   http                    rtmp
bluray                  httpproxy               rtmpe
cache                   https                   rtmps
concat                  icecast                 rtmpt
concatf                 ipfs_gateway            rtmpte
crypto                  ipns_gateway            rtmpts
data                    librist                 rtp
fd                      libsrt                  srtp
ffrtmpcrypt             libssh                  subfile
ffrtmphttp              libzmq                  tcp
file                    md5                     tee
ftp                     mmsh                    tls
gopher                  mmst                    udp
gophers                 pipe                    udplite
hls                     prompeg

Enabled filters:
a3dscope                deband                  pan
aap                     deblock                 perlin
abench                  decimate                perms
abitscope               deconvolve              perspective
acompressor             dedot                   phase
acontrast               deesser                 photosensitivity
acopy                   deflate                 pixdesctest
acrossfade              deflicker               pixelize
acrossover              deinterlace_qsv         pixscope
acrusher                deinterlace_vaapi       pp7
acue                    dejudder                premultiply
addroi                  delogo                  prewitt
adeclick                denoise_vaapi           prewitt_opencl
adeclip                 deshake                 procamp_vaapi
adecorrelate            deshake_opencl          program_opencl
adelay                  despill                 pseudocolor
adenorm                 detelecine              psnr
aderivative             dialoguenhance          pullup
adrawgraph              dilation                qp
adrc                    dilation_opencl         qrencode
adynamicequalizer       displace                qrencodesrc
adynamicsmooth          doubleweave             quirc
aecho                   drawbox                 random
aemphasis               drawbox_vaapi           readeia608
aeval                   drawgraph               readvitc
aevalsrc                drawgrid                realtime
aexciter                drawtext                remap
afade                   drmeter                 remap_opencl
afdelaysrc              dynaudnorm              removegrain
afftdn                  earwax                  removelogo
afftfilt                ebur128                 repeatfields
afir                    edgedetect              replaygain
afireqsrc               elbg                    reverse
afirsrc                 entropy                 rgbashift
aformat                 epx                     rgbtestsrc
afreqshift              eq                      roberts
afwtdn                  equalizer               roberts_opencl
agate                   erosion                 rotate
agraphmonitor           erosion_opencl          rubberband
ahistogram              estdif                  sab
aiir                    exposure                scale
aintegral               extractplanes           scale2ref
ainterleave             extrastereo             scale_cuda
alatency                fade                    scale_qsv
alimiter                feedback                scale_vaapi
allpass                 fftdnoiz                scale_vulkan
allrgb                  fftfilt                 scdet
allyuv                  field                   scdet_vulkan
aloop                   fieldhint               scharr
alphaextract            fieldmatch              scroll
alphamerge              fieldorder              segment
amerge                  fillborders             select
ametadata               find_rect               selectivecolor
amix                    firequalizer            sendcmd
amovie                  flanger                 separatefields
amplify                 flip_vulkan             setdar
amultiply               flite                   setfield
anequalizer             floodfill               setparams
anlmdn                  format                  setpts
anlmf                   fps                     setrange
anlms                   framepack               setsar
anoisesrc               framerate               settb
anull                   framestep               sharpness_vaapi
anullsink               freezedetect            shear
anullsrc                freezeframes            showcqt
apad                    frei0r                  showcwt
aperms                  frei0r_src              showfreqs
aphasemeter             fspp                    showinfo
aphaser                 fsync                   showpalette
aphaseshift             gblur                   showspatial
apsnr                   gblur_vulkan            showspectrum
apsyclip                geq                     showspectrumpic
apulsator               gradfun                 showvolume
arealtime               gradients               showwaves
aresample               graphmonitor            showwavespic
areverse                grayworld               shuffleframes
arls                    greyedge                shufflepixels
arnndn                  guided                  shuffleplanes
asdr                    haas                    sidechaincompress
asegment                haldclut                sidechaingate
aselect                 haldclutsrc             sidedata
asendcmd                hdcd                    sierpinski
asetnsamples            headphone               signalstats
asetpts                 hflip                   signature
asetrate                hflip_vulkan            silencedetect
asettb                  highpass                silenceremove
ashowinfo               highshelf               sinc
asidedata               hilbert                 sine
asisdr                  histeq                  siti
asoftclip               histogram               smartblur
aspectralstats          hqdn3d                  smptebars
asplit                  hqx                     smptehdbars
ass                     hstack                  sobel
astats                  hstack_qsv              sobel_opencl
astreamselect           hstack_vaapi            sofalizer
asubboost               hsvhold                 spectrumsynth
asubcut                 hsvkey                  speechnorm
asupercut               hue                     split
asuperpass              huesaturation           spp
asuperstop              hwdownload              sr_amf
atadenoise              hwmap                   ssim
atempo                  hwupload                ssim360
atilt                   hwupload_cuda           stereo3d
atrim                   hysteresis              stereotools
avectorscope            iccdetect               stereowiden
avgblur                 iccgen                  streamselect
avgblur_opencl          identity                subtitles
avgblur_vulkan          idet                    super2xsai
avsynctest              il                      superequalizer
axcorrelate             inflate                 surround
azmq                    interlace               swaprect
backgroundkey           interlace_vulkan        swapuv
bandpass                interleave              tblend
bandreject              join                    telecine
bass                    kerndeint               testsrc
bbox                    kirsch                  testsrc2
bench                   ladspa                  thistogram
bilateral               lagfun                  threshold
bilateral_cuda          latency                 thumbnail
biquad                  lenscorrection          thumbnail_cuda
bitplanenoise           lensfun                 tile
blackdetect             libplacebo              tiltandshift
blackdetect_vulkan      libvmaf                 tiltshelf
blackframe              life                    tinterlace
blend                   limitdiff               tlut2
blend_vulkan            limiter                 tmedian
blockdetect             loop                    tmidequalizer
blurdetect              loudnorm                tmix
bm3d                    lowpass                 tonemap
boxblur                 lowshelf                tonemap_opencl
boxblur_opencl          lumakey                 tonemap_vaapi
bs2b                    lut                     tpad
bwdif                   lut1d                   transpose
bwdif_cuda              lut2                    transpose_opencl
bwdif_vulkan            lut3d                   transpose_vaapi
cas                     lutrgb                  transpose_vulkan
ccrepack                lutyuv                  treble
cellauto                mandelbrot              tremolo
channelmap              maskedclamp             trim
channelsplit            maskedmax               unpremultiply
chorus                  maskedmerge             unsharp
chromaber_vulkan        maskedmin               unsharp_opencl
chromahold              maskedthreshold         untile
chromakey               maskfun                 uspp
chromakey_cuda          mcdeint                 v360
chromanr                mcompand                vaguedenoiser
chromashift             median                  varblur
ciescope                mergeplanes             vectorscope
codecview               mestimate               vflip
color                   metadata                vflip_vulkan
color_vulkan            midequalizer            vfrdet
colorbalance            minterpolate            vibrance
colorchannelmixer       mix                     vibrato
colorchart              monochrome              vidstabdetect
colorcontrast           morpho                  vidstabtransform
colorcorrect            movie                   vif
colorhold               mpdecimate              vignette
colorize                mptestsrc               virtualbass
colorkey                msad                    vmafmotion
colorkey_opencl         multiply                volume
colorlevels             negate                  volumedetect
colormap                nlmeans                 vpp_amf
colormatrix             nlmeans_opencl          vpp_qsv
colorspace              nlmeans_vulkan          vstack
colorspace_cuda         nnedi                   vstack_qsv
colorspectrum           noformat                vstack_vaapi
colortemperature        noise                   w3fdif
compand                 normalize               waveform
compensationdelay       null                    weave
concat                  nullsink                xbr
convolution             nullsrc                 xcorrelate
convolution_opencl      openclsrc               xfade
convolve                oscilloscope            xfade_opencl
copy                    overlay                 xfade_vulkan
corr                    overlay_cuda            xmedian
cover_rect              overlay_opencl          xpsnr
crop                    overlay_qsv             xstack
cropdetect              overlay_vaapi           xstack_qsv
crossfeed               overlay_vulkan          xstack_vaapi
crystalizer             owdenoise               yadif
cue                     pad                     yadif_cuda
curves                  pad_opencl              yaepblur
datascope               pad_vaapi               yuvtestsrc
dblur                   pal100bars              zmq
dcshift                 pal75bars               zoneplate
dctdnoiz                palettegen              zoompan
ddagrab                 paletteuse              zscale

Enabled bsfs:
aac_adtstoasc           h264_mp4toannexb        pgs_frame_merge
apv_metadata            h264_redundant_pps      prores_metadata
av1_frame_merge         hapqa_extract           remove_extradata
av1_frame_split         hevc_metadata           setts
av1_metadata            hevc_mp4toannexb        showinfo
chomp                   imx_dump_header         text2movsub
dca_core                media100_to_mjpegb      trace_headers
dovi_rpu                mjpeg2jpeg              truehd_core
dts2pts                 mjpega_dump_header      vp9_metadata
dump_extradata          mov2textsub             vp9_raw_reorder
dv_error_marker         mpeg2_metadata          vp9_superframe
eac3_core               mpeg4_unpack_bframes    vp9_superframe_split
evc_frame_merge         noise                   vvc_metadata
extract_extradata       null                    vvc_mp4toannexb
filter_units            opus_metadata
h264_metadata           pcm_rechunk

Enabled indevs:
dshow                   lavfi                   openal
gdigrab                 libcdio                 vfwcap

Enabled outdevs:
caca

git-full external libraries' versions: 

AMF v1.4.36-2-gd7311e3
aom v3.12.1-182-g6c4010bde3
aribb24 v1.0.3-5-g5e9be27
aribcaption 1.1.1
AviSynthPlus v3.7.5-22-g66f0d678
bs2b 3.1.0
chromaprint 1.5.1
codec2 1.2.0-106-g96e8a19c
dav1d 1.5.1-11-gb3c5848
davs2 1.7-1-gb41cf11
dvdnav 6.1.1-23-g9831fe0
dvdread 6.1.3-15-g786e735
ffnvcodec n13.0.19.0-1-gf2fb9b3
flite v2.2-55-g6c9f20d
freetype VER-2-13-3
frei0r v2.3.3-15-gb47c180
fribidi v1.0.16-2-gb28f43b
gsm 1.0.22
harfbuzz 11.2.1-113-g7278f8a2
ladspa-sdk 1.17
lame 3.100
lc3 1.1.3
lcms2 2.16
lensfun v0.3.95-1678-gfcbfbf38
libass 0.17.4
libcdio-paranoia 10.2
libgme 0.6.4
libilbc v3.0.4-346-g6adb26d4a4
libjxl v0.11-snapshot-298-ge4776518
libopencore-amrnb 0.1.6
libopencore-amrwb 0.1.6
libplacebo v7.351.0-12-gcaa3ceb
libsoxr 0.1.3
libssh 0.11.1
libtheora 1.2.0
libwebp v1.5.0-47-g753ed11e
openal-soft utils
openapv v0.1.13.1-39-g98e55dd
OpenCL-Headers v2025.06.13
openmpt libopenmpt-0.6.23-2-g2ee2c7f7d
opus v1.5.2-119-gc0eb2ca5
qrencode 4.1.1
quirc 1.2
rav1e p20250603-2-g105f07b
rist 0.2.12
rubberband v1.8.1
SDL release-2.32.0-55-g9eb50a906
shaderc v2025.2-1-ga5a8caa
shine 3.1.1
snappy 1.2.2
speex Speex-1.2.1-47-ga145463
srt v1.5.4-35-gd6d0e5a
SVT-AV1 v3.0.2-76-gcf44d0ae
twolame 0.4.0
uavs3d v1.1-47-g1fd0491
VAAPI 2.23.0.
vidstab v1.1.1-16-gd5a313a
vmaf v3.0.0-112-gb9ac69e6
vo-amrwbenc 0.1.3
vorbis v1.3.7-10-g84c02369
VPL 2.15
vpx v1.15.2-90-g686bf6f1c
vulkan-loader v1.4.318
vvenc v1.13.1-71-gdfe28ce
x264 v0.165.3222
x265 4.1-172-gcd40fe75d
xavs2 1.4
xevd 0.5.0
xeve 0.5.1
xvid v1.3.7
zeromq 4.3.5
zimg release-3.0.5-206-gbde53c0
zvbi v0.2.44

