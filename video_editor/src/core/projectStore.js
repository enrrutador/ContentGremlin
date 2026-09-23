// projectStore.js - persistencia local proyectos JSON
import { promises as fs } from 'fs';
import { join } from 'path';
const PROJECTS_DIR = './projects';
export async function saveProject(proj){
  await fs.mkdir(PROJECTS_DIR,{recursive:true});
  await fs.writeFile(join(PROJECTS_DIR,`${proj.id}.json`), JSON.stringify(proj,null,2));
}
export async function loadProject(id){
  const data = await fs.readFile(join(PROJECTS_DIR,`${id}.json`),'utf-8');
  return JSON.parse(data);
}
