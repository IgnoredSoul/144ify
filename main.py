import ffmpeg, os, argparse

#region Args

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "-i",
    "--input",
    help = "Input file",
    required = True
)
parser.add_argument(
    "-o",
    "--output",
    help = "Output path",
    required = True
)
parser.add_argument(
    "-fps",
    "--frames",
    help = "Frame rate",
    default = "29.79"
)
parser.add_argument(
    "-vq",
    "--videoquality",
    help = "Video quality",
    default = "28"
)
parser.add_argument(
    "-aq",
    "--audioquality",
    help = "Audio quality",
    default = "28"
)

parser.add_argument(
    "-ka",
    "--keepaspectratio",
    help = "Keeps the same width and height of the original video",
    action = "store_true"
)

#endregion

def compress_video_and_audio(i:str, o:str, vq:int, aq:int, f:int, a:bool) -> None:
    # Split the input file path to create the output file path
    base, ext = os.path.splitext(i)
    output_video_path = f"{o}/{base.rsplit('\\', 1)[1]}144Ify{ext}" # Output video name
    output_audio_path = f"{base}_audio.aac" # Tmp output audio name
    temp_video_path = f"{base}_temp_video.mp4" # Tmp output video name

    try:
        # Step 1: Compress the video to 144p quality while retaining the original resolution
        probe = ffmpeg.probe(i)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video') # Wowzers

        # Scale down to 144p and then back up to the original resolution
        if(a):
            (                
                ffmpeg
                .input(i)
                .filter('scale', -2, 144)  # Scale down to 144p (height = 144, width auto-adjusted)
                .filter('scale', int(video_info['width']), int(video_info['height']))  # Scale back up to original resolution
                .output(temp_video_path, vcodec='libx264', crf=vq, pix_fmt='yuv420p', r=f)
                .run()
            )
        else:
            (
                ffmpeg
                .input(i)
                .filter('scale', -2, 144)  # Scale down to 144p (height = 144, width auto-adjusted)
                #.filter('scale', int(video_info['width']), int(video_info['height']))  # Scale back up to original resolution
                .output(temp_video_path, vcodec='libx264', crf=vq, pix_fmt='yuv420p', r=f)
                .run()
            )

        # Step 2: Extract and compress the audio
        (
            ffmpeg
            .input(i)
            .output(output_audio_path, acodec='aac', audio_bitrate=f'{aq}K')
            .run()
        )

        # Step 3: Combine the compressed video and audio into the final output file
        (
            ffmpeg
            .concat(ffmpeg.input(temp_video_path), ffmpeg.input(output_audio_path), v=1, a=1)
            .output(output_video_path, vcodec='libx264', crf=vq, acodec='aac', audio_bitrate=f'{aq}K', strict='experimental', shortest=None)
            .run()
        )
        
        # Clean up temporary files
        os.remove(temp_video_path)
        os.remove(output_audio_path)

        print(f"Video saved as: {output_video_path}")

    except ffmpeg.Error as e:
        print (f"An error occurred:\n{e.stdout}\n I dont fucking know.")
        raise

if __name__ == "__main__":
    args = parser.parse_args()

    # Sanitize file path
    if (args.input.startswith('"') and args.input.endswith('"')) or (args.input.startswith("'") and args.input.endswith("'")):
        args.input = args.input[1:-1]
    
    # Control the video quality
    if 0 <= int(args.videoquality) <= 51:
        args.videoquality = 51 - int( args.videoquality)
    else:
        raise ValueError("Video quality value is out of range (0 - 51)")
    
    compress_video_and_audio(args.input, args.output, int(args.videoquality), int(args.audioquality), float(args.frames) if '.' in args.frames else int(args.frames), bool(args.keepaspectratio))
    
# This whole ass thing is so fucking dumb.
# Why do I do this to myself.