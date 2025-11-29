import { describe, it, expect } from "bun:test";
import Fuse from "fuse.js";

// Mock Data
const MOCK_SEGMENTS = [
    { text: "enabled, which is much better suited for production services compared to Docker Compose." },
    { text: "it's still running. This is because Docker Stack has support for rolling releases," },
    { text: "Docker Stack specification are shared, which means there are documented configuration options" },
    { text: "Next, you'll notice for the file property, this is actually set to docker-stack.yaml." },
    { text: "Initially, I achieved this by using Docker Compose, defining my entire application stack inside" },
    { text: "and Docker Compose with the start-first update ordering. In fact, another feature that Docker" },
    { text: "secure secrets, service rollbacks, and even clustering. Not only this, but when combined with Docker" },
    { text: "database. In addition to having the Docker file and Docker Compose already defined, the application" },
    { text: "followed by running the Docker stack deploy command, we can see that it's deployed successfully." },
    // Distractors
    { text: "This is a random sentence about nothing." },
    { text: "Another random sentence that mentions doc but not the full word." },
    { text: "Doctors are cool but not relevant here." }
];

describe("Search Relevance", () => {
    it("should find 'docker' with strict settings", () => {
        // Proposed Config
        const options = {
            keys: ['text'],
            includeMatches: true,
            threshold: 0.2, // Stricter threshold
            ignoreLocation: true,
            minMatchCharLength: 3
        };

        const fuse = new Fuse(MOCK_SEGMENTS, options);
        const results = fuse.search("docker");

        // Assert we found results
        expect(results.length).toBeGreaterThan(0);

        // Assert top results contain "docker" (case-insensitive)
        const topResults = results.slice(0, 5);
        topResults.forEach((res, idx) => {
            const text = res.item.text.toLowerCase();
            expect(text).toContain("docker");
        });

        // Assert we didn't match "Doctors" (or it's ranked very low)
        // Let's check if "Doctors" is in the top results
        const doctorsMatch = topResults.find(r => r.item.text.includes("Doctors"));
        expect(doctorsMatch).toBeUndefined();
    });

    it("should fail with loose settings (demonstration)", () => {
        // Current/Bad Config
        const options = {
            keys: ['text'],
            includeMatches: true,
            threshold: 0.6, // Very loose
            ignoreLocation: true
        };

        const fuse = new Fuse(MOCK_SEGMENTS, options);
        const results = fuse.search("docker");

        // This might match "doc" or "Doctors" highly
        // We just want to see what happens, but for a test we usually assert correctness.
        // Let's just log the count for info.
        console.log(`Loose search found ${results.length} results.`);
    });
});
