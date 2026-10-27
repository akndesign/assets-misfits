import bpy,math,shutil,json
from pathlib import Path
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'balanced-studio-review/balanced-studio-candidate.blend'))
s=bpy.context.scene
# Preserve the scene lighting and colour management. Composite the display-referred
# background after the AgX transform so the border is the exact requested sRGB hex.
s.render.film_transparent=True;s.render.resolution_x=3840;s.render.resolution_y=2160;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='16'
s.cycles.samples=256;s.cycles.adaptive_threshold=.007;s.render.use_persistent_data=False
floor=bpy.data.objects['Subtle charcoal contact surface'];m=floor.active_material;n=m.node_tree.nodes;l=m.node_tree.links
bs=n.get('Principled BSDF');out=n.get('Material Output')
# Fade the same receiving surface into transparency before any frame edge. No horizon.
tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Window'],sep.inputs[0])
def mathnode(op,a,b):
 q=n.new('ShaderNodeMath');q.operation=op
 for i,v in enumerate([a,b]):
  if isinstance(v,(float,int)):q.inputs[i].default_value=v
  else:l.new(v,q.inputs[i])
 return q.outputs[0]
x=mathnode('MULTIPLY',mathnode('SUBTRACT',sep.outputs['X'],.5),2)
y=mathnode('MULTIPLY',mathnode('SUBTRACT',sep.outputs['Y'],.5),2)
r=mathnode('SQRT',mathnode('ADD',mathnode('MULTIPLY',x,x),mathnode('MULTIPLY',y,y)),0)
fade=n.new('ShaderNodeMapRange');fade.clamp=True;fade.interpolation_type='SMOOTHERSTEP';l.new(r,fade.inputs['Value']);fade.inputs['From Min'].default_value=.10;fade.inputs['From Max'].default_value=.93;fade.inputs['To Min'].default_value=1;fade.inputs['To Max'].default_value=0
trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');vertical=n.new('ShaderNodeMapRange');vertical.clamp=True;vertical.interpolation_type='SMOOTHERSTEP';l.new(sep.outputs['Y'],vertical.inputs['Value']);vertical.inputs['From Min'].default_value=.40;vertical.inputs['From Max'].default_value=.80;vertical.inputs['To Min'].default_value=1;vertical.inputs['To Max'].default_value=0
alpha=mathnode('MULTIPLY',mathnode('MULTIPLY',fade.outputs[0],vertical.outputs[0]),.42);l.new(alpha,mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(bs.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
s.render.use_simplify=False;s.cycles.texture_limit='OFF'
def linear(v):
 v=v/255
 return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

# Broader, lower-energy fixed lamps: preserve the wood-only softbox.
bpy.data.objects['key'].data.energy=1100
bpy.data.objects['key'].data.size=13
bpy.data.objects['Stationary overhead soft fill'].data.energy=3000
bpy.data.objects['Stationary overhead soft fill'].data.size=16
bpy.data.objects['spine'].data.energy=10
bs.inputs['Base Color'].default_value=tuple(linear(v)*22 for v in [2,26,25])+(1,)
s.render.dither_intensity=0
# A restrained world-fixed bounce lifts only the sleeve shadow.
from mathutils import Vector
ld=bpy.data.lights.new('Soft left sleeve bounce','AREA');ld.energy=450;ld.shape='DISK';ld.size=10
lo=bpy.data.objects.new('Soft left sleeve bounce',ld);s.collection.objects.link(lo);lo.location=(-16,-2,10);lo.rotation_euler=(Vector((-10,0,0))-lo.location).to_track_quat('-Z','Y').to_euler()
receivers=bpy.data.collections.new('Sleeve bounce receivers');receivers.objects.link(bpy.data.objects['Sleeve']);lo.light_linking.receiver_collection=receivers
# Keep the full-texture editable still candidate intact.
# Keep scene-linear precision through rendering; composite exact display RGB after AgX.
import numpy as np, zlib, struct, sys
D=O/'frames';D.mkdir(exist_ok=True)
R=O/'rgba16';R.mkdir(exist_ok=True)
def compose(src,dst):
 im=bpy.data.images.load(str(src),check_existing=False)
 w,h=im.size;v=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(v);v=v.reshape(h,w,4)[::-1].copy()
 rgb=v[:,:,:3];rgb=np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)
 a=v[:,:,3:4];bg=np.array([2,26,25],dtype=np.float32)/255
 rgb=rgb*a+bg*(1-a)
 # Sub-LSB triangular dither only where the render contributes; exact borders stay flat.
 rng=np.random.default_rng(917);noise=(rng.random((h,w,1))+rng.random((h,w,1))-1)*.7/255
 rgb+=noise*(a>0.00001)
 out=np.uint8(np.clip(np.floor(rgb*255+.5),0,255))
 out[0,:,:]=[2,26,25];out[-1,:,:]=[2,26,25];out[:,0,:]=[2,26,25];out[:,-1,:]=[2,26,25]
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 raw=b''.join(b'\0'+row.tobytes() for row in out)
 dst.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))
 bpy.data.images.remove(im)

for action in bpy.data.actions:
 for fc in action.fcurves:
  for k in fc.keyframe_points:
   co=k.co.copy();lh=k.handle_left.copy();rh=k.handle_right.copy();k.co.x=1+(co.x-1)*1.25;k.handle_left.x=1+(lh.x-1)*1.25;k.handle_right.x=1+(rh.x-1)*1.25
  fc.update()
s.render.fps=60;s.render.fps_base=1;s.frame_start=1;s.frame_end=305
s.render.use_motion_blur=True;s.render.motion_blur_shutter=.5
s.cycles.use_adaptive_sampling=True;s.cycles.use_denoising=True
if not (O/'approved-4k60.blend').exists():bpy.ops.wm.save_as_mainfile(filepath=str(O/'approved-4k60.blend'))
full='--full' in sys.argv
frames=range(1,306) if full else [1,170,305]
import time
def report(**kw):
 (O/'status.json').write_text(json.dumps(dict(total=305,resolution=[3840,2160],fps=60,updated=time.time(),**kw),indent=2))
try:
 for f in frames:
  target=D/f'{f:04d}.png'
  if target.exists() and target.stat().st_size>100000:continue
  free=shutil.disk_usage(O).free
  if free<2_000_000_000:raise RuntimeError('Disk space below 2GB guard')
  report(phase='Rendering full film' if full else 'Checking 4K representative frames',frame=f,completed=len(list(D.glob('*.png'))),free_bytes=free)
  s.frame_set(f);src=R/f'{f:04d}.png';s.render.filepath=str(src);bpy.ops.render.render(write_still=True);compose(src,target)
 report(phase='Frames ready for encoding' if full else '4K proofs ready for inspection',completed=len(list(D.glob('*.png'))))
except Exception as e:
 report(phase='Blocked',error=str(e),completed=len(list(D.glob('*.png'))));raise
