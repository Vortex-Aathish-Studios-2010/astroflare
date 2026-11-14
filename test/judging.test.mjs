import test from 'node:test';import fs from 'node:fs';import {researchJudgeChecks} from './judge-helpers.mjs';
const html=fs.readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
for(const width of [1280,390])test('judge regression matrix, rapid submissions, blank cancellation, filter accounting, comparison, brief and history at DOM width '+width,async()=>{await researchJudgeChecks(html,{width});});
