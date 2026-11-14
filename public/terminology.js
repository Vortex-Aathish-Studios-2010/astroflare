// Presentation-only terminology correction. Original engine numbers, units and source archives stay intact.
function correctAssessmentTerminology(value){
 if(typeof value==='string')return value.replace(/let[-\s\u2011\u2013]through energy(?: of the fault)?(?: \((?:I²t|I2t)\))?/gi,'fault current integral (I²t)');
 if(Array.isArray(value))return value.map(correctAssessmentTerminology);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,correctAssessmentTerminology(v)]));
 return value;
}
