from pathlib import Path
import subprocess,json,time,struct
O=Path(__file__).resolve().parent;ff=str(O/'ffmpeg');D=O/'frames'
assert len(list(D.glob('*.png')))==305
for i in range(1,306):
 p=D/f'{i:04d}.png';b=p.read_bytes();assert struct.unpack('>II',b[16:24])==(3840,2160) and b[-8:-4]==b'IEND'
status=O/'status.json'
status.write_text(json.dumps({'phase':'Encoding colour-accurate 4K RGB master','completed':305,'total':305,'fps':60}))
movie=O/'misfits-approved-4k60-rgb.mp4'
subprocess.run([ff,'-y','-loglevel','warning','-framerate','60','-start_number','1','-i',str(D/'%04d.png'),'-frames:v','305','-c:v','libx264rgb','-crf','0','-preset','medium','-threads','2','-movflags','+faststart',str(movie)],check=True)
# Verify all decoded frame borders and exact frame count. RGB lossless retains source dither.
proc=subprocess.Popen([ff,'-loglevel','error','-i',str(movie),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
import numpy as np
count=0;size=3840*2160*3
while True:
 data=proc.stdout.read(size)
 if not data:break
 assert len(data)==size
 a=np.frombuffer(data,dtype=np.uint8).reshape(2160,3840,3)
 for edge in [a[0],a[-1],a[:,0],a[:,-1]]:assert np.all(edge==[2,26,25]),f'Border mismatch frame{count+1}'
 count+=1
assert proc.wait()==0 and count==305
(O/'encode-verification.json').write_text(json.dumps({'frames':count,'resolution':[3840,2160],'fps':60,'duration':305/60,'every_decoded_border':'#021A19','encoding':'lossless RGB H264','dither':'preserved losslessly'},indent=2))
status.write_text(json.dumps({'phase':'Complete — verified RGB master','completed':305,'total':305,'fps':60,'encoded':True,'movie':movie.name}))
