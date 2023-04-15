// get iframe the simulator is running in.  Must have same origin as this file!
var iframe = document.getElementById("circuitFrame");


// constants
const POLL_SEQ_NR_SEC = 0.0000001;
const TIME_STEP_SEC = 0.0000010416666666666667;
const WEB_SOCKET_ADDR = "ws://127.0.0.1:9000";


/*
about the websocket API:
########################
	In order to reuse circuitjs as it is, we only use available" functions.
	This limits the possibilities a little bit, but it is still possible to interface external applications in a sufficient manner
	in order to keep simulation results consistent among different applications.
	Depending on the speed of the external application it may be necessary to slow down the simulation speed in circuitjs.
	
	The list of available API functions can be found in setupJSInterface() here:
	https://github.com/pfalstad/circuitjs1/blob/master/src/com/lushprojects/circuitjs1/client/CirSim.java

		setSimRunning: $entry(function(run) { that.@com.lushprojects.circuitjs1.client.CirSim::setSimRunning(Z)(run); } ),
		getTime: $entry(function() { return that.@com.lushprojects.circuitjs1.client.CirSim::t; } ),
		getTimeStep: $entry(function() { return that.@com.lushprojects.circuitjs1.client.CirSim::timeStep; } ),
		setTimeStep: $entry(function(ts) { that.@com.lushprojects.circuitjs1.client.CirSim::timeStep = ts; } ),
		isRunning: $entry(function() { return that.@com.lushprojects.circuitjs1.client.CirSim::simIsRunning()(); } ),
		getNodeVoltage: $entry(function(n) { return that.@com.lushprojects.circuitjs1.client.CirSim::getLabeledNodeVoltage(Ljava/lang/String;)(n); } ),
		setExtVoltage: $entry(function(n, v) { that.@com.lushprojects.circuitjs1.client.CirSim::setExtVoltage(Ljava/lang/String;D)(n, v); } ),
		getElements: $entry(function() { return that.@com.lushprojects.circuitjs1.client.CirSim::getJSElements()(); } ),
		getCircuitAsSVG: $entry(function() { return that.@com.lushprojects.circuitjs1.client.CirSim::doExportAsSVGFromAPI()(); } ),
		exportCircuit: $entry(function() { return that.@com.lushprojects.circuitjs1.client.CirSim::dumpCircuit()(); } ),
		importCircuit: $entry(function(circuit, subcircuitsOnly) { return that.@com.lushprojects.circuitjs1.client.CirSim::importCircuitFromText(Ljava/lang/String;Z)(circuit, subcircuitsOnly); })
		
	The list of available methods to access elements can be found in addJSMethods() here:
	https://github.com/pfalstad/circuitjs1/blob/master/src/com/lushprojects/circuitjs1/client/CircuitElm.java
	
		this.getType = $entry(function() { return that.@com.lushprojects.circuitjs1.client.CircuitElm::getClassName()(); });
        this.getInfo = $entry(function() { return that.@com.lushprojects.circuitjs1.client.CircuitElm::getInfoJS()(); });
        this.getVoltageDiff = $entry(function() { return that.@com.lushprojects.circuitjs1.client.CircuitElm::getVoltageDiff()(); });
        this.getVoltage = $entry(function(n) { return that.@com.lushprojects.circuitjs1.client.CircuitElm::getVoltageJS(I)(n); });
        this.getCurrent = $entry(function() { return that.@com.lushprojects.circuitjs1.client.CircuitElm::getCurrent()(); });
        this.getLabelName = $entry(function() { return that.@com.lushprojects.circuitjs1.client.LabeledNodeElm::getName()(); });
        this.getPostCount = $entry(function() { return that.@com.lushprojects.circuitjs1.client.CircuitElm::getPostCount()(); });
*/


// ########################################################
var socket = null;
var isopen = false;
var seqNrTx = 0;
var seqNrRx = 0;
var MAX_SEQ_NR = 2**8;
var curr_time = 0;
var curr_voltage = 0;


window.onload = function() 
{
    socket = new WebSocket(WEB_SOCKET_ADDR);
	socket.binaryType = "arraybuffer";

    socket.onopen = function() 
    {
		console.log("Connected!");
        isopen = true;	
    } 

    socket.onmessage = function(e) 
    {       
		if (typeof e.data == "string") 
		{
			telFields = e.data.split(',');
			if(parseInt(telFields[0]) == seqNrRx)
			{			
		        // TODO: set Vs in didStep() instead (using an intermediate module variable)?
				sim.setExtVoltage("Vs", parseFloat(telFields[1]));
				
				seqNrRx = (seqNrRx + 1)%MAX_SEQ_NR;		
				// NOTE: using the values curr_time and curr_voltage set in didStep() improves performance from 900Hz to 1400Hz
				//       use current values:
				//       socket.send(seqNrTx + "," + round(sim.getTime()*1000) + ";" + round(elm_Ve.getVoltage(0)));
				// use values set in didStep():			
				socket.send(seqNrTx + "," + round(curr_time*1000) + ";" + round(curr_voltage));
				seqNrTx = (seqNrTx + 1)%MAX_SEQ_NR;
			}
			else
			{
				console.log("WARNING: SeqNr mismatch. SeqNrRx = " + parseInt(telFields[0]) + ", but SeqNr expected = " + seqNrRx.toString())
			}
		}
   }

   socket.onclose = function(e) 
   {
		console.log("Connection closed.");
		socket = null;
		isopen = false;
   }
};
// ########################################################

var updateNr = 0;
var UPDATE_PERIOD = 10;

var sim;
var elm_Vs; // value sent to python app over websocket
var elm_Ve; // value received from python app over websocket
var elm_Tr; // transformer element
var elm_R = []; // resistor elements
var elm_switch; // set by python app over websocket


async function sleep(ms) 
{
  return new Promise(resolve => setTimeout(resolve, ms));
}

function round(x) 
{
  return Math.round(x*1000)/1000;
}

// called when simulator updates its display
function didUpdate(sim) 
{	
  if(updateNr == 0)
  {  
      var info = document.getElementById("info");
	  // general infos
	  info.innerHTML = "time [ms] = " + round(sim.getTime()*1000) + "<br>seqNr TX, RX = " + round(seqNrTx) + ", " + round(seqNrRx) + "<br>running = " + sim.isRunning(); 
	  // circuit elements
	  info.innerHTML += "<br>V(Vs) = " + round(elm_Vs.getVoltage(0));
	  info.innerHTML += "<br>V(Ve) = " + round(elm_Ve.getVoltage(0));
	  info.innerHTML += "<br>Transformer Vprim = " + round(elm_Tr.getVoltage(0));
	  for (var i = 0; i < elm_R.length; i++) 
	  {	  
		info.innerHTML += "<br>resistor " + i + " voltage diff = " + round(elm_R[i].getVoltageDiff());
		info.innerHTML += "<br>resistor " + i + " current = " + round(elm_R[i].getCurrent() * 1000) + " mA";	  
	  }
	  // console.log("## V(Vs) = " + round(elm_Vs.getVoltage(0)));
	  // console.log("## V(Ve) = " + round(elm_Ve.getVoltage(0)));
	  // console.log("## Transformer Vprim = " + round(elm_Tr.getVoltage(0)));
  }
  updateNr = (updateNr +1)%UPDATE_PERIOD;
}

// called when simulator analyzes a circuit (when a circuit is loaded or edited)
function didAnalyze(sim) 
{
  console.log("analyzing circuit..");

  // get the list of elements
  var elmList = [];
  elmList = sim.getElements();
  var rcount = 0;

  // log some info about each one
  for (const elm of elmList) 
  {
    console.log("elm " + elm.getType() + ", " + elm.getPostCount() + " posts");
    console.log("elm info: " + elm.getInfo());
	
    // initialize variables containing the circuit elements
    if (elm.getType() == "LabeledNodeElm") 
	{
      if (elm.getLabelName() == "Ve") 
	  {
        elm_Ve = elm;
      }
    }
	else if (elm.getType() == "ExtVoltageElm")
	{	
	  // if (elm.getLabelName() == "Vs") // ???
	  {
        elm_Vs = elm;
      }
	}
	else if (elm.getType() == "TransformerElm") 
	{ 
	  // if (elm.getLabelName() == "xx") // ???
	  {
		elm_Tr = elm;
	  }
	}
    else if (elm.getType() == "SwitchElm") 
	{
      elm_switch = elm;
    }
	else if (elm.getType() == "ResistorElm") 
	{
      elm_R[rcount] = elm;
	  rcount++;
    } 
  }
  
  // set time step
  console.log("time step before = " + sim.getTimeStep());
  // NOTE: this does not update the menu entry which still shows the default value...
  sim.setTimeStep(TIME_STEP_SEC);
  console.log("time step after  = " + sim.getTimeStep());
  
  // set up further callbacks now that we are done with the initial analysis
  sim.onupdate = didUpdate;
  
  console.log("circuit analyzed!");
  
  // send initial message to App
  if (isopen)
  {		
		console.log("sending initial message..");
		socket.send(seqNrTx + "," + round(sim.getTime()*1000) + ";" + round(elm_Ve.getVoltage(0)));	  		  
		seqNrTx = (seqNrTx + 1)%MAX_SEQ_NR;
  }
  else
  {
	  console.log("Error: initial message could not be sent because the websocket is closed!")
  }	
}

// called in each time step
function didStep(sim)
{
	// if (isopen) // NOTE: don't need to check this 
	{
		curr_time = sim.getTime();
		curr_voltage = elm_Ve.getVoltage(0);
	}
}

// callback called when simulation is done initializing
function simLoaded() 
{
    // get simulator object
    sim = iframe.contentWindow.CircuitJS1;
    // set up callbacks on update and timestep
    // sim.onupdate = didUpdate; // NOTE: we set this later inside didAnalyze() in order to first analyse everything before we start updating
    sim.ontimestep = didStep; // NOTE: this callback is not needed if we just answer the message received over websocket in onmessage() using the values at that moment
    sim.onanalyze = didAnalyze;
}

// set up callback
iframe.contentWindow.oncircuitjsloaded = simLoaded;





