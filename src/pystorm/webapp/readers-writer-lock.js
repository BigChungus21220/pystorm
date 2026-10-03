/*
MIT License

Copyright (c) 2019 Domokos Kelen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

'use strict'

let locknum = 0

async function sleep(t){
	return await new Promise(r=>setTimeout(r, t))
}

async function executeAndResolve(f, resolve){
	try {
		let result = await f()
		resolve()
		return result
	} catch(e){
		resolve()
		throw e
	}
}

class Lock {
	constructor(){
		this.order = locknum++
		this.lock_promise = null
		this.locked = false
	}
	async run(f){
		let resolve = null
		let previous_lock = this.lock_promise
		this.lock_promise = new Promise((rs,rj)=>{
			resolve = rs
		})
		// we need to set the flag before awaiting since await could give control
		// to other parts of the codebase
		this.locked = true
		await previous_lock
		// we need to set it again, since if the previous lock just unlocked, then
		// it sets it to false
		this.locked = true
		return await executeAndResolve(f, ()=>{
			this.locked=false
			resolve()
		})
	}

	async run_or_fail(f){
		// need to give up control to allow locking by code in the same synchronous
		// code block
		await new Promise((resolve) => process.nextTick(() => resolve()));
		if(this.locked){
			throw "locked"
		} else {
			return await this.run(f)
		}
	}
}

class CombinedLock {
	constructor(locks){
		this.locks = locks.sort(function(l1, l2){
			return l1.order - l2.order
		}).reverse()
	}
	async run(f){
		let work = f
		let self = this
		this.locks.forEach(function(lock, i, arr){
			let old_word = work
			work = async () => {
				return await lock.run(old_word)
			}
		})
		return await work()
	}
}

class RWLock {
	constructor(){
		this.meta_lock = new Lock()
		this.writing_promise = null
		this.reading_promises = []
	}
	async read(f){
		let resolve = null
		await this.meta_lock.run(async ()=>{
			await this.writing_promise
			this.reading_promises.push(new Promise((rs,rj)=>{
				resolve = rs
			}))
		})
		return await executeAndResolve(f, resolve)
	}
	async write(f){
		let resolve = null
		await this.meta_lock.run(async ()=>{
			await this.writing_promise
			await Promise.all(this.reading_promises)
			this.writing_promise = new Promise((rs, rj)=>{
				resolve = rs
			})
			this.reading_promises = []
		})
		return await executeAndResolve(f, resolve)
	}
}

function combine(locks){
	return new CombinedLock(locks)
}

/*module.exports = {
	Lock,
	CombinedLock,
	RWLock,
	sleep,
	combine,
}*/