import os
import re
import subprocess
from datetime import datetime
import torch
from num2words import num2words
class TTS :
    default_init ={
    "sample_rate":24000 ,
    "device_init":"cpu",
    "threads":4 ,
    "speaker_voice":"kseniya",
    "model_path":"models/silero/model.pt",
    "model_url":"https://models.silero.ai/models/tts/ru/v3_1_ru.pt",
    "ffmpeg_path":"models/silero"
    }
    def __init__ (
    self ,
    sample_rate =None ,
    device_init =None ,
    threads =None ,
    speaker_voice =None ,
    model_path =None ,
    model_url =None ,
    ffmpeg_path =None
    )->None :
        self .sample_rate =sample_rate if sample_rate else TTS .default_init ["sample_rate"]
        self .device_init =device_init if device_init else TTS .default_init ["device_init"]
        self .threads =threads if threads else TTS .default_init ["threads"]
        self .speaker_voice =speaker_voice if speaker_voice else TTS .default_init ["speaker_voice"]
        self .model_path =model_path if model_path else TTS .default_init ["model_path"]
        self .model_url =model_url if model_url else TTS .default_init ["model_url"]
        self .ffmpeg_path =ffmpeg_path if ffmpeg_path else TTS .default_init ["ffmpeg_path"]
        self ._check_model ()
        device =torch .device (self .device_init )
        torch .set_num_threads (self .threads )
        self .model =torch .package .PackageImporter (self .model_path ).load_pickle ("tts_models","model")
        self .model .to (device )
    def _check_model (self ):
        if not os .path .isfile (self .model_path ):
            torch .hub .download_url_to_file (self .model_url ,self .model_path )
        isffmpeg_here =False
        for file in os .listdir (self .ffmpeg_path ):
            if file .startswith ('ffmpeg'):
                isffmpeg_here =True
        if not isffmpeg_here :
            raise Exception (
            "Ffmpeg: сохраните ffmpeg.exe в папку ffmpeg\n"
            "Скачайте ffmpeg.exe по ссылке https://ffmpeg.org/download.html"
            )
        self .ffmpeg_path =self .ffmpeg_path +'/ffmpeg'
    def wav_to_ogg (
    self ,
    in_filename :str ,
    out_filename :str =None
    )->str :
        if not in_filename :
            raise Exception ("Укажите путь и имя файла in_filename")
        if out_filename is None :
            out_filename ="test_1.ogg"
        if os .path .exists (out_filename ):
            os .remove (out_filename )
        command =[
        self .ffmpeg_path ,
        "-loglevel","quiet",
        "-i",in_filename ,
        "-acodec","libvorbis",
        out_filename
        ]
        proc =subprocess .Popen (
        command ,
        stdout =subprocess .DEVNULL ,
        stderr =subprocess .DEVNULL
        )
        proc .wait ()
        return out_filename
    def ogg_to_wav (
    self ,
    in_filename :str ,
    out_filename :str =None
    )->str :
        if not in_filename :
            raise Exception ("Укажите путь и имя файла in_filename")
        if out_filename is None :
            out_filename ="test_1.wav"
        if os .path .exists (out_filename ):
            os .remove (out_filename )
        command =[
        self .ffmpeg_path ,
        "-i",in_filename ,
        "-ar","16000",
        "-ac","1",
        "-c:a","pcm_s16le",
        out_filename
        ]
        proc =subprocess .Popen (
        command ,
        stdout =subprocess .DEVNULL ,
        stderr =subprocess .DEVNULL
        )
        proc .wait ()
        return out_filename
    def _get_wav (self ,text :str ,speaker_voice =None ,sample_rate =None )->str :
        if text is None :
            raise Exception ("Передайте текст")
        if os .path .exists ("test.wav"):
            os .remove ("test.wav")
        if speaker_voice is None :
            speaker_voice =self .speaker_voice
        if sample_rate is None :
            sample_rate =self .sample_rate
        return self .model .save_wav (
        text =text ,
        speaker =speaker_voice ,
        sample_rate =sample_rate
        )
    def _get_ogg (self ,text :str ,speaker_voice =None ,sample_rate =None )->str :
        wav_audio_path =self ._get_wav (text ,speaker_voice ,sample_rate )
        ogg_audio_path =self .wav_to_ogg (wav_audio_path )
        if os .path .exists (wav_audio_path ):
            os .remove (wav_audio_path )
        return ogg_audio_path
    def _nums_to_text (self ,text :str )->str :
        return re .sub (
        r"(\d+)",
        lambda x :num2words (int (x .group (0 )),lang ="ru"),
        text )
    def _merge_audio_n_to_1 (
    self ,
    in_filenames :list ,
    out_filename :str =None
    )->str :
        if not in_filenames :
            raise Exception ("Укажите пути и имя файла in_filenames")
        if out_filename is None :
            extension =in_filenames [0 ].split (sep =".")[-1 ]
            out_filename =f"test_n_1.{extension }"
        if os .path .exists (out_filename ):
            os .remove (out_filename )
        filenames ="\n".join ([f"file '{filename }'"for filename in in_filenames ])
        with open ("audiolist.txt","wt")as file :
            file .write (filenames )
        command =[
        self .ffmpeg_path ,
        "-loglevel","quiet",
        "-f","concat",
        "-safe","0",
        "-i","audiolist.txt",
        "-c","copy",
        out_filename ,
        ]
        proc =subprocess .Popen (command )
        proc .wait ()
        if os .path .exists ("audiolist.txt"):
            os .remove ("audiolist.txt")
        return out_filename
    def _rename_file (self ,in_filename :str ,out_filename :str )->str :
        if in_filename is None or out_filename is None :
            raise Exception ("Передайте названия входного и выходного файла")
        if os .path .exists (out_filename ):
            os .remove (out_filename )
        os .rename (in_filename ,out_filename )
        return out_filename
    def text_to_ogg (self ,text :str ,out_filename :str =None )->str :
        if text is None :
            raise Exception ("Передайте текст")
        text =self ._nums_to_text (text )
        if len (text )<800 :
            ogg_audio_path =self ._get_ogg (text )
            if out_filename is None :
                return ogg_audio_path
            return self ._rename_file (ogg_audio_path ,out_filename )
        texts =[text [x :x +800 ]for x in range (0 ,len (text ),800 )]
        files =[]
        for index in range (len (texts )):
            ogg_audio_path =self ._get_ogg (texts [index ])
            new_ogg_audio_path =f"{index }_{ogg_audio_path }"
            os .rename (ogg_audio_path ,new_ogg_audio_path )
            files .append (new_ogg_audio_path )
        ogg_audio_path =self ._merge_audio_n_to_1 (files ,out_filename ="test_n_1.ogg")
        [os .remove (file )for file in files ]
        if out_filename is None :
            return ogg_audio_path
        return self ._rename_file (ogg_audio_path ,out_filename )
    def text_to_wav (self ,text :str ,out_filename :str =None )->str :
        if text is None :
            raise Exception ("Передайте текст")
        text =self ._nums_to_text (text )
        if len (text )<800 :
            wav_audio_path =self ._get_wav (text )
            if out_filename is None :
                return wav_audio_path
            return self ._rename_file (wav_audio_path ,out_filename )
        texts =[text [x :x +800 ]for x in range (0 ,len (text ),800 )]
        files =[]
        for index in range (len (texts )):
            wav_audio_path =self ._get_wav (texts [index ])
            new_wav_audio_path =f"{index }_{wav_audio_path }"
            os .rename (wav_audio_path ,new_wav_audio_path )
            files .append (new_wav_audio_path )
        wav_audio_path =self ._merge_audio_n_to_1 (files ,out_filename ="test_n_1.wav")
        [os .remove (file )for file in files ]
        if out_filename is None :
            return wav_audio_path
        return self ._rename_file (wav_audio_path ,out_filename )
    def wav_to_ogg_bytes (self ,in_bytes :bytes )->bytes :
        command =[
        self .ffmpeg_path ,
        "-i",'pipe:0',
        "-f","ogg",
        "-acodec","libvorbis",
        "pipe:1"
        ]
        proc =subprocess .Popen (
        command ,
        stdin =subprocess .PIPE ,
        stdout =subprocess .PIPE ,
        stderr =subprocess .PIPE
        )
        out_bytes ,err =proc .communicate (input =in_bytes )
        return out_bytes
if __name__ =="__main__":
    start_time =datetime .now ()
    tts =TTS ()
    print (tts .text_to_ogg ("Привет,Хабр! Тэст 1 2 три четыре","test-1.ogg"))
    print (tts .text_to_wav ("Тэст! Как меня слышно? Пыш-пыш. Прием!","test-2.wav"))
    print (tts .text_to_ogg ("Слышу хорошо! Пыш-пыш.","test-3.ogg"))
    print ("Время выполнения:",datetime .now ()-start_time )