export async function createProject(name='Untitled'){
  return {id:'uuid', name, media:[], timeline:{tracks:[]}};
}
export async function getProject(id){ return null; }
