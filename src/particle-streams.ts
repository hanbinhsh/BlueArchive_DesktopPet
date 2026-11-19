// Unity packs enabled streams consecutively into TEXCOORD registers.
// UV/UV2 occupy two scalars each; Custom2 may be present without Custom1.
export function particleShaderData(streams: number[] | undefined, data: number[][]): number[][] {
 if(!Array.isArray(streams))return data;
 const packed:number[]=[];
 for(const stream of streams){
  if(stream>=4&&stream<=7)packed.push(0,0);
  else if(stream>=31&&stream<=38){const group=stream<35?0:1,count=(stream-(group?35:31))+1;packed.push(...data[group].slice(0,count));}
  else if(stream>3)return data; // Other layouts retain their existing adapter.
 }
 while(packed.length<12)packed.push(0);
 return [packed.slice(4,8),packed.slice(8,12)];
}
