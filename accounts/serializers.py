from rest_framework import serializers

class AuthSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['register', 'login', 'refresh'],
        help_text="Action to perform: register, login, or refresh"
    )

    # Fields
    username = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)
    refresh = serializers.CharField(write_only=True, required=False)
    turnstileToken = serializers.CharField(write_only=True, required=False)  # ✅ added token field

    def validate(self, attrs):
        action = attrs.get('action')

        if action == 'register':
            required_fields = ['phone', 'turnstileToken']  # ✅ require token for registration
        elif action == 'login':
            required_fields = ['username', 'password']
        elif action == 'refresh':
            required_fields = ['refresh']
        else:
            required_fields = []

        missing = [f for f in required_fields if not attrs.get(f)]
        if missing:
            raise serializers.ValidationError({
                field: f"This field is required for {action}"
                for field in missing
            })

        return attrs
