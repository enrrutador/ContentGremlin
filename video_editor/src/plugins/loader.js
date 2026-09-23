// loader.js - carga y valida manifiestos de plugins
import { promises as fs } from 'fs';
import { join } from 'path';
export async function loadCatalog(){
  const data = await fs.readFile(join('./plugins/catalog.json'),'utf-8');
  return JSON.parse(data);
}
export function validateManifest(manifest){
  return !!manifest.id && !!manifest.name && !!manifest.version;
}
