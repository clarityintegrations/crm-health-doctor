// Consume real Python adapter/service rejection envelopes, not handcrafted UI mocks.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {execFileSync} from 'node:child_process';
const root = new URL('../', import.meta.url);
const cases = JSON.parse(execFileSync('python3', ['-m', 'tests.test_readiness_adversarial', '--ui-cases'],
  {cwd: root, env: {...process.env, PYTHONDONTWRITEBYTECODE:'1'}, encoding:'utf8'}));
const source = fs.readFileSync(new URL('../readiness/ui.js', import.meta.url), 'utf8');
function node() {
  return {textContent:'', children:[], disabled:false, value:'C-008', handlers:{},
    appendChild(n) {this.children.push(n);}, replaceChildren() {this.children=[];this.textContent='';},
    addEventListener(e,f) {this.handlers[e]=f;}};
}
assert.equal(cases.length,13);
for (const {name,envelope} of cases) {
  const nodes = Object.fromEntries(['alias','assess','status','evidence','assessment'].map(id=>[id,node()]));
  nodes.alias.value=envelope.evidence.record.alias;
  vm.runInNewContext(source,{document:{getElementById:id=>nodes[id],createElement:()=>node()},encodeURIComponent,
    fetch:async url=>({ok:true,json:async()=>url.startsWith('/evidence')?envelope.evidence:envelope})});
  await new Promise(resolve=>setImmediate(resolve));
  await nodes.assess.handlers.click();
  assert.equal(envelope.error_code,'invalid_assessment',name);
  assert.equal(nodes.assessment.children.length,0,name);
  assert.ok(nodes.evidence.children.length>0,name);
  assert.match(nodes.status.textContent,/unavailable/,name);
  assert.equal(nodes.assess.disabled,false,name);
}
console.log('All 13 production-path adversarial envelopes fail safely in unchanged UI.');
