const evtSource = new EventSource("/events");

let PLACEHOLDER = "_placeholder"

// required due to event system
let effectLock = new RWLock();
let particleCache = undefined;
const effects = new Map();
let activeEffect = undefined;
const View = {};

let thumbLock = new Lock();
let thumbCanvas = new OffscreenCanvas(512, 512);
let thumbCtx = thumbCanvas.getContext('webgl2', { alpha: false });

window.addEventListener('resize', resizeCanvas, false);

// app entry point
// organized to minimize time to active particle loading
async function initializeApp() {
	particleCache = await caches.open('particle-cache')
	await effectLock.write(async function(){
		await getEffect(PLACEHOLDER, false);
	});

	sceneSetup();
	resizeCanvas();

	await effectLock.write(async function(){
		await setActiveEffect((await loadJSON("active.json")).active)
	});

	// start event listeners
	evtSource.addEventListener("file_update", (e) => {
		onFileUpdate(JSON.parse(e.data));
	});

	evtSource.addEventListener("view_change", (e) => {
		onViewChange(JSON.parse(e.data));
	});

	evtSource.addEventListener("remove_effect", (e) => {
		onRemoveEffect(JSON.parse(e.data));
	});

	evtSource.addEventListener("clear_library", (e) => {
		onClearLibrary(JSON.parse(e.data));
	});

	// create gallery
	const registry = await loadJSON("effects.json");
	await effectLock.write(async function(){
		for (const [effect, data] of Object.entries(registry)) {
			if (!effects.has(effect)) {
				await getEffect(effect, false);
			}
		}
		await buildGallery();
	});
}

// must be write locked
// takes url safe particle identifier (: replaced with ~)
// returns [particle json, base64 texture]
async function getEffect(effect, doBuildGallery=true) {
    const particle_url = `${effect}.particle.json`;
	const additional_url = `${effect}.additional.json`;
    const texture_url = `${effect}.png`;

	let update = false
	if (effects.has(effect)) {
		try {
			const [particle_res, additional_res, texture_res] = await Promise.all([
				particleCache.match(particle_url),
				particleCache.match(additional_url),
				particleCache.match(texture_url)
			]);

			if (!particle_res || !additional_res || !texture_res) {
				throw new Error("Cache miss");
			}

			particle = await particle_res.json();
			additional = await additional_res.json();
			texture = await texture_res.text();

		} catch (e) {
			console.error(`Cache miss on effect: '${effect}'. Using fallback.`);
			return await getEffect(PLACEHOLDER);
		}

	} else {
		try {
			[particle, additional, texture] = await Promise.all([loadJSON(particle_url), loadJSON(additional_url), loadPNG(texture_url)]);
		} catch (e) {
			console.error(`Request failed on effect: '${effect}'. Using fallback.`);
			return await getEffect(PLACEHOLDER);
		}

		update = true
	}

	if (update) {
		particleCache.put(
			particle_url, 
			new Response(JSON.stringify(particle), { 
				headers: { 'Content-Type': 'application/json' } 
			})
		);
		particleCache.put(
			additional_url, 
			new Response(JSON.stringify(additional), { 
				headers: { 'Content-Type': 'application/json' } 
			})
		);
		particleCache.put(
			texture_url, 
			new Response(texture)
		);

		effects.set(effect, {
			identifier: particle.particle_effect.description.identifier,
			thumbnail: undefined
		})

		if (doBuildGallery) {
			await buildGallery();
		}
	}

	return [particle, additional, texture]
}

// must be write locked
// updates the sidebar gallery to sync with the currently loaded effects
async function buildGallery() {
	const grid = document.getElementById("gallery_grid");

	let content = "";
	for (const [effect, data] of [...effects.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {

		if (data.thumbnail === undefined) {
			const [particle, additional, texture] = await getEffect(effect);

			const id = particle.particle_effect.description.identifier;
			if (id == '') continue;

			data.thumbnail = await renderThumbnail(particle, texture);

			effects.get(effect).thumbnail = data.thumbnail;
			effects.get(effect).identifier = id;
		}
		const classes = activeEffect == effect ? "gallery-item active" : "gallery-item";
		content += `
		<div class="${classes}" name="${effect}" onclick="setActiveEffect('${effect}')">
			<img src="${data.thumbnail}" class="thumbnail"></img>
			<div class="item-title-box">
				<div class="item-title">${data.identifier}</div>
			</div>
			<div class="item-source-box">
				<div class="item-source">${"source" in additional ? additional.source.split('.', 1)[0] : ""}</div>
			</div>
		</div>`;
	}

	grid.innerHTML = content;
}

// sets up the Three.js scene
function sceneSetup() {
	View.canvas = document.getElementById('preview')
	View.camera = new THREE.PerspectiveCamera(45, 16/9, 0.1, 3000);
	View.camera.position.set(-6, 3, -6)
	View.renderer = new THREE.WebGLRenderer({
		canvas: View.canvas,
		antialias: true,
		alpha: true,
		preserveDrawingBuffer: true,
	})

	View.controls = new THREE.OrbitControls(View.camera, View.canvas);
	View.controls.target.set(0, 0.8, 0)
	View.controls.screenSpacePanning = true;
	View.controls.zoomSpeed = 1.4;

	View.scene = new THREE.Scene()
	View.scene.background = new THREE.Color('#14141a');

	View.helper = new THREE.AxesHelper(1);
	View.grid = new THREE.GridHelper(64, 64, '#686767', '#717171');
	View.grid.position.y -= 0.0005
	View.scene.add(View.helper);
	View.scene.add(View.grid);
}

function animate() {
	requestAnimationFrame(animate);
	View.controls.update();
	// Update Particle facing rotation
	View.wintersky.updateFacingRotation(View.camera);
	// Render
	View.renderer.render(View.scene, View.camera);
}

// must be write locked
// updates the displayed effect given a url safe id
async function setActiveEffect(effect) {
	let [particle, additional, texture] = await getEffect(effect);

	activeEffect = effect;

	const identifier_display = document.getElementById("info_identifier");
	identifier_display.innerText = particle.particle_effect.description.identifier;
	
	// update selected gallery item
	const grid = document.getElementById("gallery_grid");
	for (let elm of grid.children) {
		if (elm.getAttribute('name') == activeEffect){
			elm.classList.add("active");
		} else {
			elm.classList.remove("active");
		}
	}

	// update renderer
	if (View.wintersky) {
		View.wintersky._fetchTexture = (config) => texture;
	} else {
		View.wintersky = new Wintersky.Scene({
			fetchTexture: (config) => texture
		})
		View.scene.add(View.wintersky.space);
		animate();
	}

	if (View.emitter) {
		View.emitter.stop(true);
		View.emitter.config.reset().setFromJSON(particle);
	} else {
		View.emitter = new Wintersky.Emitter(View.wintersky, particle, {loop_mode:"looping"});
	}

	View.emitter.playLoop();

	console.log("view updated")
}

// renders a thumbnail
// currently not working for some reason
async function renderThumbnail(particle, texture) {
	return await thumbLock.run(async function(){
		let camera = new THREE.PerspectiveCamera(20, 1/1, 0.1, 3000);
		camera.position.set(-9, 3, -9);
		camera.lookAt(0,1,0);
		let renderer = new THREE.WebGLRenderer({
			canvas: thumbCanvas,
			context: thumbCtx,
			antialias: true,
			alpha: true,
			preserveDrawingBuffer: true,
		})

		let scene = new THREE.Scene()
		scene.background = new THREE.Color('#14141a');

		let helper = new THREE.AxesHelper(1);
		let grid = new THREE.GridHelper(64, 64, '#222222', '#222222');
		grid.position.y -= 0.01
		scene.add(helper);
		scene.add(grid);
		
		let wintersky = new Wintersky.Scene({
			fetchTexture: (config) => texture
		})
		scene.add(wintersky.space);

		let emitter = new Wintersky.Emitter(wintersky, particle);

		let jumpTime = 0.1;
		let particle_lifetime = particle.particle_effect.components["minecraft:particle_lifetime_expression"]
		if (particle_lifetime && particle_lifetime.max_lifetime !== undefined) {
			let ftime = parseFloat(particle_lifetime.max_lifetime);
			if (ftime) jumpTime = ftime/2;
		}

		emitter.jumpTo(jumpTime);
		wintersky.updateFacingRotation(camera);
		renderer.render(scene, camera);

		return blobToBase64(await thumbCanvas.convertToBlob());
	})
}


///////////////
// callbacks //
///////////////

function resizeCanvas() {
	var canvas = View.canvas;
	var height = canvas.clientHeight;
	var width = canvas.clientWidth;

	View.camera.aspect = width/height;
	View.camera.updateProjectionMatrix();

	View.renderer.setSize(width, height, false);
	View.renderer.setPixelRatio(window.devicePixelRatio);
}

function killServer() {
	fetch("/shutdown", { method: 'POST' });
	window.location.reload();
}

function toggleGallery() {
	const gallery_container = document.getElementById("gallery_container");
	if (gallery_container.classList.contains("open")) {
		gallery_container.classList.remove("open");
	} else {
		gallery_container.classList.add("open");
	}
	resizeCanvas();
}

// loads a new file and caches it
async function onFileUpdate(event) {
	const url = (event.type == "particle") ? `${event.effect}.particle.json` : ((event.type == "aditional") ? `${event.effect}.additional.json` : `${event.effect}.png`);
	try {
		await effectLock.write(async function(){
			if (event.type == "particle") {
				const url = `${event.effect}.particle.json`;
				const particle = await loadJSON(url);
				particleCache.put(
					url, 
					new Response(JSON.stringify(particle), { 
						headers: { 'Content-Type': 'application/json' } 
					})
				);

				effects.set(event.effect, {
					identifier: particle.particle_effect.description.identifier,
					thumbnail: undefined
				});

			} else if (event.type == "additional") {
				const url = `${event.effect}.addtional.json`;
				const addtional = await loadJSON(url);
				particleCache.put(
					url, 
					new Response(JSON.stringify(additional), { 
						headers: { 'Content-Type': 'application/json' } 
					})
				);
			} else {
				const url = `${event.effect}.png`;
				const texture = await loadPNG(url);
				particleCache.put(url, new Response(texture));

				effects.get(event.effect).thumbnail = undefined;
			}

			if (activeEffect == event.effect || activeEffect == PLACEHOLDER) {
				await setActiveEffect(event.effect);
			}

			await buildGallery();
		})

 	} catch (e) {
		console.error(`Request failed loading file: '${url}'.`);
    }
}

async function onViewChange(event) {
	await effectLock.write(async function(){
		await setActiveEffect(event.active)
	})
}

async function onClearLibrary(event) {
	await effectLock.write(async function(){
		let placeholder = effects.get(PLACEHOLDER)
		effects.clear()
		effects.set(PLACEHOLDER, placeholder)

		for (request in await particleCache.keys()) {
			if (request.url != `${PLACEHOLDER}.particle.json` && request.url != `${PLACEHOLDER}.png`) {
				particleCache.delete(request)
			}
		}

		await setActiveEffect(event.active)

		await buildGallery()
	})
}

async function onRemoveEffect(event) {
	await effectLock.write(async function(){
		if (event.effect != PLACEHOLDER){
			effects.delete(event.effect)

			particleCache.delete(`${event.effect}.particle.json`)
			particleCache.delete(`${event.effect}.png`)

			await setActiveEffect(event.active)

			await buildGallery()
		}
	})
}


/////////////
// helpers //
/////////////

async function loadJSON(path) {
	let content = await new Promise((resolve, reject) => {
		var xhr = new XMLHttpRequest();
		xhr.open('GET', path, true);
		xhr.responseType = 'json';
		xhr.onload = function() {
			var status = xhr.status;
			if (status === 200) {
				resolve(xhr.response);
			} else {
				reject(xhr.response);
			}
		};
		xhr.send();
	})
	return content;
}

function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

async function loadPNG(path) {
	const response = await fetch(path);
	const blob = await response.blob();

	return blobToBase64(blob);
}