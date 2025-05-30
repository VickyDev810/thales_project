from app.pipeline.pipeline import detect_pii
from app.pipeline.anonymizer import anonymize_text


text = """
Hey Jordan, make sure to push the final build to `vault-prod-east` before midnight. Also, let Ravi know we updated the heuristics in the SentinelShield module — this version finally filters legacy device IDs. 

Keep the credentials out of the Slack thread — especially not the one ending in `72df` from the `priv-keys-export.xlsx` file. You can use my backup access token if needed: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`.

BTW, Rebecca’s personal number is still 415-555-0132, and she prefers we use her protonmail: reb.secure@pm.me when discussing anything related to Project Vanta or that investor data dump from Q2.

Oh, and don't mention the AI bias audit results in the all-hands — just forward them to Miriam securely.

Cheers.

"""

text_small = (
    "Hi, I'm Alex. My number is 555-321-1234. Let's connect. "
    "And if you got to do a payment use my card 4216 8701 5010 2349"
)

text_llm = {
     "steps to setup google places api the credential are eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
}
# file = open("sample_response.txt", "w")
# file.write(str(result))
# file.close()
def run():
    result = detect_pii(text, "all")


    for detector, matches in result.items():
            print(f"\n-- {detector.upper()} DETECTOR RESULTS --")
            if not matches:
                print("No matches found.")
            else:
                for i, match in enumerate(matches, 1):
                    print(f"{i}. {match}")

    all_pii = []
    for mode_results in result.values():
        all_pii.extend(mode_results)

    redacted_text = anonymize_text(text, all_pii, "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApnhE8fu37rR2kHQM6k+S\n16qPjZNWnfYqETuG/j7DNlE74WPsp74awWNNg72byuK44TFVNCmqy6vz7b5i8VTe\nxrEvjM0y6ldBMou09ZQC3Z5kuWTJ1bDh07bH3Vj0FugJ3eulT+BXA2k1I+hwTfEa\nELkLjOb6Lt1a4gDs4OjFUAl4KyM/PRzR3uHR0+dilNuMJ/hrXMqFGaHOFqLNYjSD\n9omGjJVMShlO/xoZ07/CE1nKj/4fGFJFyxG7ZKLZoVsnE4NWEz35JwYmnbqJWGOZ\nBhWI1Zsw5cH8EWsJuG1f8KivgKahZS7IJe+rTm0BPHKSpPa3XY8P1DI1wyyKMhQ0\nNwIDAQAB\n-----END PUBLIC KEY-----")


    print(redacted_text)
