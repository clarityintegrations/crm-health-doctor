import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync(new URL('../readiness/ui.js', import.meta.url), 'utf8');
function node() {
  return {textContent:'', children:[], disabled:false, value:'C-008', handlers:{},
    appendChild(n) {this.children.push(n);}, replaceChildren() {this.children=[];this.textContent='';},
    addEventListener(e, f) {this.handlers[e]=f;}};
}
const nodes = Object.fromEntries(['alias','assess','status','evidence','assessment'].map(id=>[id,node()]));
const evidence = {record:{alias:'C-008'},audit_metadata:{finding_count:1,highest_priority:95},
  findings:[{finding_type:'missing_owner',finding_id:'C-008:missing_owner',evidence:{detail:'Owner absent.'}}],observations:[]};
let behavior='success';
const requests=[];
const claim = {statement:'<script>unsafe()</script>',basis:'inference',rationale:'Review required.',evidence_references:['C-008:missing_owner']};
const assessment={overall_readiness_score:null,confidence:'low',dimension_scores:{data:null,process:null,knowledge:null,governance:null,integrations:null},
 dimension_assessments:Object.fromEntries(['data','process','knowledge','governance','integrations'].map(d=>[d,claim])),
 critical_blockers:[claim],viable_agent_opportunities:[],conditional_agent_opportunities:[],not_ready_agent_opportunities:[],remediation_priorities:[],recommended_next_actions:[],evidence_gaps:[],limitations:['Synthetic only']};
vm.runInNewContext(source,{document:{getElementById:id=>nodes[id],createElement:()=>node()},encodeURIComponent,
 fetch:async(url,options)=>{
  requests.push({url,options});
  if(url.startsWith('/evidence')) return {ok:true,json:async()=>evidence};
  if(behavior==='network') throw Error('unsafe provider detail');
  return {ok:true,json:async()=>({evidence,status:behavior==='success'?'available':'unavailable',
   message:behavior==='success'?'Review required':'AI readiness assessment unavailable.',assessment,
   provenance:{model:'gpt-6-astra',duration_seconds:12,completed_at:'2026-09-16'}})};
 }});
await new Promise(resolve=>setImmediate(resolve));
await nodes.assess.handlers.click();
assert.ok(nodes.assessment.children.length>0);
assert.match(JSON.stringify(nodes.assessment.children),/<script>unsafe/);
assert.doesNotMatch(source,/innerHTML|insertAdjacentHTML|eval\(/);
for(const mode of ['unavailable','network']) {
 behavior=mode;await nodes.assess.handlers.click();
 assert.equal(nodes.assessment.children.length,0);
 assert.ok(nodes.evidence.children.length>0);
 assert.match(nodes.status.textContent,/unavailable/);
 assert.equal(nodes.assess.disabled,false);
}
assert.ok(requests.every(r=>r.url.startsWith('/')));
console.log('Readiness UI tests passed: success, escaped text, unavailable, transport failure.');
